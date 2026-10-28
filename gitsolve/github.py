# gitSOLVE ✦ GitHub API Client with ETag Caching & Rate-Limit Resilience
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

from gitsolve.config import get_config_dir, load_config

def get_cache_db_path() -> Path:
    return get_config_dir() / "cache.db"

GITHUB_API_BASE = "https://api.github.com"

def _init_cache_db() -> None:
    db_path = get_cache_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                url TEXT PRIMARY KEY,
                etag TEXT,
                status_code INTEGER,
                body TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        _init_cache_db()
        cfg = load_config()
        self.token = token or os.environ.get("GITHUB_TOKEN") or cfg.get("github_token", "").strip()
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "gitSOLVE-Radar/0.1.0",
        })
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _get_cached(self, url: str) -> Optional[Tuple[str, int, str]]:
        try:
            with sqlite3.connect(get_cache_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT etag, status_code, body FROM api_cache WHERE url = ?", (url,))
                return cursor.fetchone()
        except Exception:
            return None

    def _save_cache(self, url: str, etag: Optional[str], status_code: int, body: str) -> None:
        try:
            with sqlite3.connect(get_cache_db_path()) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache (url, etag, status_code, body, cached_at) VALUES (?, ?, ?, ?, ?)",
                    (url, etag or "", status_code, body, datetime.now().isoformat())
                )
                conn.commit()
        except Exception:
            pass

    def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Dict[str, Any]:
        url = endpoint if endpoint.startswith("http") else f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
        headers = {}
        
        cache_entry = self._get_cached(url) if use_cache and method.upper() == "GET" and not params else None
        if cache_entry and cache_entry[0]:
            headers["If-None-Match"] = cache_entry[0]

        try:
            resp = self.session.request(method, url, params=params, headers=headers, timeout=12)
        except requests.RequestException as e:
            if cache_entry:
                return json.loads(cache_entry[2])
            raise RuntimeError(f"Network error connecting to GitHub: {e}")

        # If cache matched
        if resp.status_code == 304 and cache_entry:
            return json.loads(cache_entry[2])

        # Rate limited
        if resp.status_code in (403, 429):
            reset_time = resp.headers.get("X-RateLimit-Reset")
            reset_msg = ""
            if reset_time:
                try:
                    delta = int(reset_time) - int(time.time())
                    if delta > 0:
                        reset_msg = f" (Resets in {delta // 60}m {delta % 60}s)"
                except Exception:
                    pass
            if not self.token:
                raise RuntimeError(
                    f"GitHub rate limit exceeded for unauthenticated requests{reset_msg}. "
                    "Run `/config` to add a GitHub Personal Access Token for 5,000 requests/hour."
                )
            raise RuntimeError(f"GitHub rate limit exceeded{reset_msg}.")

        if resp.status_code >= 400:
            error_data = {}
            try:
                error_data = resp.json()
            except Exception:
                pass
            msg = error_data.get("message", f"HTTP {resp.status_code}")
            raise RuntimeError(f"GitHub API error: {msg}")

        text = resp.text
        if use_cache and method.upper() == "GET" and not params:
            etag = resp.headers.get("ETag")
            self._save_cache(url, etag, resp.status_code, text)

        try:
            return resp.json()
        except Exception:
            return {"raw": text}

    def search_repositories(self, query: str, sort: str = "updated", order: str = "desc", per_page: int = 15, page: int = 1) -> Dict[str, Any]:
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page,
        }
        return self.request("GET", "/search/repositories", params=params, use_cache=False)

    def get_repo(self, full_name: str) -> Dict[str, Any]:
        return self.request("GET", f"/repos/{full_name}")

    def get_commits(self, full_name: str, per_page: int = 15) -> List[Dict[str, Any]]:
        res = self.request("GET", f"/repos/{full_name}/commits", params={"per_page": per_page})
        return res if isinstance(res, list) else []

    def get_contents(self, full_name: str, path: str = "") -> List[Dict[str, Any]]:
        res = self.request("GET", f"/repos/{full_name}/contents/{path.lstrip('/')}")
        return res if isinstance(res, list) else [res]

    def get_readme(self, full_name: str) -> Optional[str]:
        try:
            res = self.request("GET", f"/repos/{full_name}/readme")
            import base64
            content = res.get("content", "")
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            return None

    def get_tree(self, full_name: str, branch: str = "HEAD") -> List[Dict[str, Any]]:
        try:
            res = self.request("GET", f"/repos/{full_name}/git/trees/{branch}", params={"recursive": "1"})
            return res.get("tree", [])
        except Exception:
            return []

    def get_rate_limit(self) -> Dict[str, Any]:
        return self.request("GET", "/rate_limit")
