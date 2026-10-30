# gitSOLVE ✦ Hardened GitHub API Client with ETag Caching, Backoff & Resilience
import json
import os
import random
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

from gitsolve.config import get_config_dir, load_config
from gitsolve.security import sanitize_text

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_CACHE_TTL = 3600  # 1 hour cache TTL for dynamic queries

def get_cache_db_path() -> Path:
    return get_config_dir() / "cache.db"

from contextlib import contextmanager

@contextmanager
def _get_cache_connection():
    db_path = get_cache_db_path()
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def _init_cache_db() -> None:
    try:
        with _get_cache_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    url TEXT PRIMARY KEY,
                    etag TEXT,
                    status_code INTEGER,
                    body TEXT,
                    cached_at TEXT,
                    ttl_seconds INTEGER DEFAULT 3600
                )
            """)
            conn.commit()
    except Exception:
        pass

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        _init_cache_db()
        cfg = load_config()
        self.token = token or os.environ.get("GITHUB_TOKEN") or cfg.get("github_token", "").strip()
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "gitSOLVE-Radar/0.3.0 (Software for Humans)",
        })
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_limit: Optional[int] = None
        self.rate_limit_reset: Optional[int] = None
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def get_rate_limit_summary(self) -> str:
        if self.rate_limit_remaining is not None and self.rate_limit_limit is not None:
            return f"{self.rate_limit_remaining}/{self.rate_limit_limit}"
        return "5k/hr" if self.token else "60/hr"

    def _get_cached(self, url: str) -> Optional[Tuple[str, int, str, str, int]]:
        try:
            with _get_cache_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT etag, status_code, body, cached_at, ttl_seconds FROM api_cache WHERE url = ?", (url,))
                    return cursor.fetchone()
                finally:
                    cursor.close()
        except Exception:
            return None

    def _save_cache(self, url: str, etag: Optional[str], status_code: int, body: str, ttl: int = DEFAULT_CACHE_TTL) -> None:
        try:
            with _get_cache_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache (url, etag, status_code, body, cached_at, ttl_seconds) VALUES (?, ?, ?, ?, ?, ?)",
                    (url, etag or "", status_code, body, datetime.now(timezone.utc).isoformat(), ttl)
                )
                conn.commit()
        except Exception:
            pass

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        ttl: int = DEFAULT_CACHE_TTL,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Makes an HTTP request to the GitHub API with caching, backoff, and rate limit pacing."""
        url = endpoint if endpoint.startswith("http") else f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
        headers = {}

        cache_entry = self._get_cached(url) if (use_cache and method.upper() == "GET" and not params) else None
        if cache_entry and cache_entry[0]:
            headers["If-None-Match"] = cache_entry[0]

        attempt = 0
        last_error = None

        while attempt < max_retries:
            attempt += 1
            try:
                resp = self.session.request(method, url, params=params, headers=headers, timeout=12)
            except requests.RequestException as e:
                last_error = e
                # Fallback to cache if offline
                if cache_entry and cache_entry[2]:
                    try:
                        cached_json = json.loads(cache_entry[2])
                        if isinstance(cached_json, dict):
                            cached_json["_is_stale_cache"] = True
                        return cached_json
                    except Exception:
                        pass
                if attempt < max_retries:
                    time.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
                    continue
                raise RuntimeError(f"Network error connecting to GitHub: {e}")

            # 304 Not Modified -> Serve Cache
            if "X-RateLimit-Remaining" in resp.headers:
                try:
                    self.rate_limit_remaining = int(resp.headers["X-RateLimit-Remaining"])
                    self.rate_limit_limit = int(resp.headers.get("X-RateLimit-Limit", 60 if not self.token else 5000))
                    self.rate_limit_reset = int(resp.headers.get("X-RateLimit-Reset", 0))
                except Exception:
                    pass

            if resp.status_code == 304 and cache_entry:
                try:
                    return json.loads(cache_entry[2])
                except Exception:
                    pass

            # 403 / 429 Rate Limiting
            if resp.status_code in (403, 429):
                reset_time = resp.headers.get("X-RateLimit-Reset")
                retry_after = resp.headers.get("Retry-After")
                reset_msg = ""
                if retry_after:
                    reset_msg = f" (Retry after {retry_after}s)"
                elif reset_time:
                    try:
                        delta = int(reset_time) - int(time.time())
                        if delta > 0:
                            reset_msg = f" (Resets in {delta // 60}m {delta % 60}s)"
                    except Exception:
                        pass

                # If rate limited and cache exists, serve stale cache gracefully
                if cache_entry and cache_entry[2]:
                    try:
                        cached_json = json.loads(cache_entry[2])
                        if isinstance(cached_json, dict):
                            cached_json["_is_stale_cache"] = True
                        return cached_json
                    except Exception:
                        pass

                if not self.token:
                    raise RuntimeError(
                        f"GitHub API rate limit exceeded for unauthenticated requests{reset_msg}. "
                        "Run `/config` or `gs config` to add a GitHub Personal Access Token for 5,000 requests/hour."
                    )
                raise RuntimeError(f"GitHub API rate limit exceeded{reset_msg}.")

            # 5xx Transient Server Errors -> Retry with exponential backoff
            if resp.status_code >= 500:
                if attempt < max_retries:
                    time.sleep((2 ** attempt) + random.uniform(0.1, 0.5))
                    continue
                raise RuntimeError(f"GitHub server error: HTTP {resp.status_code}")

            # 4xx Client Errors
            if resp.status_code >= 400:
                error_data = {}
                try:
                    error_data = resp.json()
                except Exception:
                    pass
                msg = error_data.get("message", f"HTTP {resp.status_code}")
                raise RuntimeError(f"GitHub API error: {msg}")

            # Successful response
            text = resp.text
            if use_cache and method.upper() == "GET" and not params:
                etag = resp.headers.get("ETag")
                self._save_cache(url, etag, resp.status_code, text, ttl=ttl)

            try:
                return resp.json()
            except Exception:
                return {"raw": text}

        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")

    def search_repositories(
        self,
        query: str,
        sort: str = "updated",
        order: str = "desc",
        per_page: int = 20,
        page: int = 1,
    ) -> Dict[str, Any]:
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page,
        }
        return self.request("GET", "/search/repositories", params=params, use_cache=False)

    def get_repo(self, full_name: str) -> Dict[str, Any]:
        clean = normalize_repo_name(full_name)
        return self.request("GET", f"/repos/{clean}")

    def get_commits(self, full_name: str, per_page: int = 15) -> List[Dict[str, Any]]:
        clean = normalize_repo_name(full_name)
        res = self.request("GET", f"/repos/{clean}/commits", params={"per_page": per_page})
        return res if isinstance(res, list) else []

    def get_contents(self, full_name: str, path: str = "") -> List[Dict[str, Any]]:
        clean = normalize_repo_name(full_name)
        res = self.request("GET", f"/repos/{clean}/contents/{path.lstrip('/')}")
        return res if isinstance(res, list) else [res]

    def get_readme(self, full_name: str) -> Optional[str]:
        """Fetches repository README with resilient multi-tier fallback (GitHub API + Raw Fallback)."""
        clean = normalize_repo_name(full_name)
        if not clean or "/" not in clean:
            return None

        # Tier 1: Official GitHub REST API
        try:
            res = self.request("GET", f"/repos/{clean}/readme")
            if isinstance(res, dict):
                import base64
                content = res.get("content", "")
                if content:
                    decoded = base64.b64decode(content).decode("utf-8", errors="replace")
                    if decoded and len(decoded.strip()) > 0:
                        return sanitize_text(decoded, max_length=30000)
                download_url = res.get("download_url")
                if download_url:
                    raw_resp = self.session.get(download_url, timeout=8)
                    if raw_resp.status_code == 200 and raw_resp.text:
                        return sanitize_text(raw_resp.text, max_length=30000)
        except Exception:
            pass

        # Tier 2: Resilient fallback to raw.githubusercontent.com (Works without API rate limits!)
        raw_candidates = [
            f"https://raw.githubusercontent.com/{clean}/HEAD/README.md",
            f"https://raw.githubusercontent.com/{clean}/main/README.md",
            f"https://raw.githubusercontent.com/{clean}/master/README.md",
            f"https://raw.githubusercontent.com/{clean}/HEAD/readme.md",
            f"https://raw.githubusercontent.com/{clean}/HEAD/README.rst",
            f"https://raw.githubusercontent.com/{clean}/HEAD/README",
        ]
        for candidate_url in raw_candidates:
            try:
                resp = self.session.get(candidate_url, timeout=6)
                if resp.status_code == 200 and resp.text and len(resp.text.strip()) > 0:
                    return sanitize_text(resp.text, max_length=30000)
            except Exception:
                continue

        return None

    def get_tree(self, full_name: str, branch: str = "HEAD") -> List[Dict[str, Any]]:
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/git/trees/{branch}", params={"recursive": "1"})
            return res.get("tree", []) if isinstance(res, dict) else []
        except Exception:
            return []

    def get_languages(self, full_name: str) -> Dict[str, int]:
        """Returns verified language byte distribution directly from GitHub."""
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/languages")
            return res if isinstance(res, dict) else {}
        except Exception:
            return {}

    def get_workflow_runs(self, full_name: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """Returns verified GitHub Actions workflow runs to check if CI actually succeeds."""
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/actions/runs", params={"per_page": per_page})
            return res.get("workflow_runs", []) if isinstance(res, dict) else []
        except Exception:
            return []

    def get_releases(self, full_name: str, per_page: int = 5) -> List[Dict[str, Any]]:
        """Returns releases/tags history."""
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/releases", params={"per_page": per_page})
            return res if isinstance(res, list) else []
        except Exception:
            return []

    def get_commit_activity(self, full_name: str) -> List[Dict[str, Any]]:
        """Returns 52 weeks of commit activity for craftsmanship cadence analysis."""
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/stats/commit_activity", ttl=6 * 3600)
            if isinstance(res, list) and res and isinstance(res[0], dict) and "days" in res[0]:
                return res
            # GitHub may answer 202 while computing stats; retry once after a short pause.
            time.sleep(1.2)
            res = self.request("GET", f"/repos/{clean}/stats/commit_activity", use_cache=False)
            return res if isinstance(res, list) else []
        except Exception:
            return []

    def get_forks(self, full_name: str, sort: str = "newest", per_page: int = 15) -> List[Dict[str, Any]]:
        """Returns active forks for fork discovery."""
        clean = normalize_repo_name(full_name)
        try:
            res = self.request("GET", f"/repos/{clean}/forks", params={"sort": sort, "per_page": per_page})
            return res if isinstance(res, list) else []
        except Exception:
            return []

    def get_rate_limit(self) -> Dict[str, Any]:
        return self.request("GET", "/rate_limit", use_cache=False)


def normalize_repo_name(raw: str) -> str:
    """Cleans URLs, git extensions, and whitespace into standard owner/repo format."""
    cleaned = raw.strip()
    for prefix in ("https://github.com/", "http://github.com/", "git@github.com:"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    cleaned = cleaned.rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    return cleaned
