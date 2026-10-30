# gitSOLVE ✦ Discovery Engine, Fork Intelligence & Forensic X-Ray Inspector
# Software for Humans. Discover the hidden internet of code.

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from gitsolve.config import load_config
from gitsolve.github import GitHubClient
from gitsolve.scoring import EvidenceStatus, RepoScoreReport, calculate_explainable_score
from gitsolve.security import sanitize_repo_data, sanitize_text
from gitsolve.vault import Vault
from gitsolve.ai import PollinationsClient

class RepoInspector:
    def __init__(
        self,
        client: Optional[GitHubClient] = None,
        vault: Optional[Vault] = None,
        ai_client: Optional[PollinationsClient] = None,
    ):
        self.client = client or GitHubClient()
        self.vault = vault or Vault()
        self.ai = ai_client or PollinationsClient()

    def inspect_repo(self, repo_data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Runs the evidence-backed forensic diagnostic on a candidate repository."""
        clean_data = sanitize_repo_data(repo_data)
        full_name = clean_data.get("full_name", "")
        stars = clean_data.get("stargazers_count", 0)
        forks = clean_data.get("forks_count", 0)
        open_issues = clean_data.get("open_issues_count", 0)
        created_at_str = clean_data.get("created_at", "")
        pushed_at_str = clean_data.get("pushed_at", "")
        description = clean_data.get("description") or ""
        primary_lang = clean_data.get("language") or "Code"
        html_url = clean_data.get("html_url", f"https://github.com/{full_name}")
        is_fork = bool(clean_data.get("fork", False))

        now = datetime.now(timezone.utc)
        created_at = None
        pushed_at = None
        age_days = 0
        pushed_days = 0
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                age_days = (now - created_at).days
            except Exception:
                pass
        if pushed_at_str:
            try:
                pushed_at = datetime.fromisoformat(pushed_at_str.replace("Z", "+00:00"))
                pushed_days = (now - pushed_at).days
            except Exception:
                pass

        if age_days >= 365:
            age_text = f"{age_days // 365}y {(age_days % 365) // 30}m old"
        elif age_days >= 30:
            age_text = f"{age_days // 30} months old"
        else:
            age_text = f"{age_days} days old"

        # Forensic telemetry containers
        has_tests = False
        has_ci_workflow = False
        ci_verified_passing = None  # None = not checked/no runs, True = verified pass, False = failing
        has_demo = False
        modern_manifest = None
        source_files_count = 0
        semantic_commits = 0
        commit_cadence_days = 0
        has_docs_guide = False
        readme_len = 0
        has_security_policy = False
        languages = {}
        parent_repo = None

        if is_fork:
            # Check parent upstream details if available in full repo payload
            parent_info = clean_data.get("parent")
            if parent_info:
                parent_repo = {
                    "full_name": parent_info.get("full_name"),
                    "stars": parent_info.get("stargazers_count", 0),
                    "html_url": parent_info.get("html_url"),
                }

        if deep:
            # 1. Languages inspection (Verified bytes)
            languages = self.client.get_languages(full_name)

            # 2. File tree inspection
            tree = self.client.get_tree(full_name)
            if tree:
                manifests = {
                    "Cargo.toml": "Rust/Cargo",
                    "pyproject.toml": "Modern Python",
                    "go.mod": "Go Module",
                    "package.json": "TypeScript/Node",
                    "CMakeLists.txt": "C/C++ CMake",
                    "Makefile": "Makefile",
                    "Dockerfile": "Containerized",
                    "flake.nix": "Nix Flake",
                    "mix.exs": "Elixir/Mix",
                    "build.zig": "Zig Build",
                }
                for item in tree:
                    path = item.get("path", "") if isinstance(item, dict) else str(item)
                    p_lower = path.lower()

                    for m_file, m_label in manifests.items():
                        if path == m_file or path.endswith("/" + m_file):
                            if not modern_manifest:
                                modern_manifest = m_label

                    if any(t_dir in p_lower for t_dir in ["test/", "tests/", "spec/", "benches/", "_test.go", ".test.ts", ".spec.ts", "test_"]):
                        has_tests = True

                    if ".github/workflows" in path or ".gitlab-ci.yml" in path:
                        has_ci_workflow = True

                    if "security.md" in p_lower or ".github/security.md" in p_lower:
                        has_security_policy = True

                    if not any(v in p_lower for v in ["node_modules", "vendor/", "dist/", "target/", ".git/"]):
                        if any(p_lower.endswith(ext) for ext in [".rs", ".py", ".go", ".ts", ".tsx", ".c", ".cpp", ".h", ".zig", ".lua", ".swift", ".kt", ".ex"]):
                            source_files_count += 1

            # 3. Actions / CI execution verification
            if has_ci_workflow:
                runs = self.client.get_workflow_runs(full_name, per_page=3)
                if runs:
                    latest_run = runs[0]
                    conclusion = latest_run.get("conclusion")
                    if conclusion == "success":
                        ci_verified_passing = True
                    elif conclusion in ("failure", "timed_out"):
                        ci_verified_passing = False

            # 4. Commit forensics
            commits = self.client.get_commits(full_name, per_page=15)
            if commits:
                semantic_regex = re.compile(r"^(feat|fix|perf|refactor|docs|test|chore|style|build|ci)(\([a-zA-Z0-9_-]+\))?:", re.IGNORECASE)
                commit_dates = []
                for c in commits:
                    msg = c.get("commit", {}).get("message", "").strip().split("\n")[0]
                    if semantic_regex.match(msg):
                        semantic_commits += 1
                    a_date = c.get("commit", {}).get("author", {}).get("date")
                    if a_date:
                        try:
                            commit_dates.append(datetime.fromisoformat(a_date.replace("Z", "+00:00")))
                        except Exception:
                            pass

                if len(commit_dates) >= 2:
                    commit_dates.sort()
                    commit_cadence_days = (commit_dates[-1] - commit_dates[0]).days

            # 5. Documentation audit
            readme = self.client.get_readme(full_name)
            if readme:
                readme_len = len(readme)
                has_code_blocks = "```" in readme
                has_demo = any(ext in readme.lower() for ext in [".gif", ".png", ".svg", ".jpg", "asciinema"])
                has_install = any(k in readme.lower() for k in ["install", "usage", "quickstart", "getting started", "setup"])
                if has_code_blocks and has_install:
                    has_docs_guide = True

        # Declared license
        lic_obj = clean_data.get("license")
        license_name = lic_obj.get("name") if isinstance(lic_obj, dict) else None

        # Calculate explainable score
        report = calculate_explainable_score(
            stars=stars,
            age_days=age_days,
            pushed_days=pushed_days,
            is_fork=is_fork,
            has_tests=has_tests,
            has_ci_workflow=has_ci_workflow,
            ci_verified_passing=ci_verified_passing,
            modern_manifest=modern_manifest,
            has_readme=bool(readme_len > 0),
            readme_len=readme_len,
            has_docs_guide=has_docs_guide,
            has_demo_assets=has_demo,
            semantic_commits=semantic_commits,
            commit_cadence_days=commit_cadence_days,
            license_declared=license_name,
            source_files_count=source_files_count,
            languages=languages,
            has_security_policy=has_security_policy,
        )

        # Mark seen in vault
        self.vault.mark_seen(full_name)

        gem_dict = {
            "full_name": full_name,
            "name": clean_data.get("name", ""),
            "author": full_name.split("/")[0] if "/" in full_name else "",
            "stars": stars,
            "forks": forks,
            "open_issues": open_issues,
            "description": description,
            "primary_language": primary_lang,
            "html_url": html_url,
            "age_text": age_text,
            "age_days": age_days,
            "pushed_days": pushed_days,
            "is_fork": is_fork,
            "parent_repo": parent_repo,
            "overall_score": report.overall_score,
            "health_score": report.health_score,
            "discovery_score": report.discovery_score,
            "sleeper_score": report.overall_score,
            "confidence": report.confidence,
            "tier": report.tier,
            "positive_evidence": report.positive_evidence,
            "negative_risks": report.negative_risks,
            "missing_data": report.missing_data,
            "evidence_status": report.evidence_status,
            "breakdown": report.breakdown,
            "has_tests": has_tests,
            "has_ci": has_ci_workflow,
            "ci_verified_passing": ci_verified_passing,
            "license": license_name,
            "loc_estimate": source_files_count * 90 if source_files_count else 0,
            "source_files_count": source_files_count,
            "languages": languages,
            "retrieved_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        }

        # Generate high-speed deterministic verdict for candidate evaluation
        if deep:
            try:
                gem_dict["ai_verdict"] = self.ai._offline_fallback_verdict(gem_dict)
            except Exception:
                pass

        return gem_dict

    def search_radar(
        self,
        topic: str = "",
        language: str = "",
        query_text: str = "",
        min_stars: int = 1,
        max_stars: int = 15,
        min_age_days: int = 45,
        max_pushed_days: int = 30,
        fork_mode: str = "exclude",  # "exclude", "include", "only"
        exclude_seen: bool = True,
        sort: str = "updated",
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Multi-dimensional discovery radar with deduplication and seen-history filters."""
        now = datetime.now(timezone.utc)
        created_before = (now - timedelta(days=min_age_days)).strftime("%Y-%m-%d")
        pushed_after = (now - timedelta(days=max_pushed_days)).strftime("%Y-%m-%d")

        q_parts = [
            f"stars:{min_stars}..{max_stars}",
            f"created:<={created_before}",
            f"pushed:>={pushed_after}",
            "archived:false",
            "size:>50",
        ]

        if fork_mode == "exclude":
            q_parts.append("fork:false")
        elif fork_mode == "only":
            q_parts.append("fork:only")
        # if include, don't restrict fork

        if topic:
            q_parts.append(f"topic:{topic.strip()}")
        if language:
            q_parts.append(f"language:{language.strip()}")
        if query_text:
            q_parts.append(query_text.strip())

        full_query = " ".join(q_parts)
        res = self.client.search_repositories(full_query, sort=sort, order="desc", per_page=min(30, limit * 3))
        items = res.get("items", [])

        # Deduplicate and optionally filter out previously reviewed repos
        seen_canonical = set()
        candidates = []
        for item in items:
            fname = item.get("full_name")
            if not fname or fname in seen_canonical:
                continue
            seen_canonical.add(fname)
            if exclude_seen and self.vault.is_seen(fname):
                continue
            candidates.append(item)
            if len(candidates) >= limit:
                break

        # If strict exclude_seen exhausted results, fall back to showing candidates
        if not candidates and items:
            candidates = items[:limit]

        inspected = []
        for c in candidates:
            try:
                gem = self.inspect_repo(c, deep=True)
                inspected.append(gem)
            except Exception:
                inspected.append(self.inspect_repo(c, deep=False))

        # Rank by overall sleeper score descending
        inspected.sort(key=lambda g: g.get("overall_score", 0), reverse=True)
        return inspected

    def search_fresh(self, language: str = "", limit: int = 8) -> List[Dict[str, Any]]:
        """Discovers meaningful recent activity and explicitly identifies the freshness reason."""
        now = datetime.now(timezone.utc)
        pushed_after = (now - timedelta(days=3)).strftime("%Y-%m-%d")

        query = f"pushed:>={pushed_after} stars:1..20 archived:false fork:false size:>50"
        if language:
            query += f" language:{language.strip()}"

        res = self.client.search_repositories(query, sort="updated", order="desc", per_page=limit * 2)
        items = res.get("items", [])

        gems = []
        for item in items[:limit]:
            gem = self.inspect_repo(item, deep=True)
            # Categorize the freshness signal
            if gem["age_days"] <= 30:
                gem["fresh_signal"] = "🌱 New Handcrafted Project"
                gem["fresh_detail"] = f"Created {gem['age_days']} days ago with immediate momentum"
            elif gem["pushed_days"] == 0:
                gem["fresh_signal"] = "⚡ Active Commit Burst"
                gem["fresh_detail"] = "Fresh code committed today"
            else:
                gem["fresh_signal"] = "🔄 Maintained Iteration"
                gem["fresh_detail"] = f"Updated {gem['pushed_days']} days ago"
            gems.append(gem)

        gems.sort(key=lambda g: g.get("overall_score", 0), reverse=True)
        return gems

    def xray_repo(self, full_name: str) -> Dict[str, Any]:
        """Deep forensic investigation of a specific repository."""
        cleaned_name = full_name.replace("https://github.com/", "").replace("http://github.com/", "").replace("git@github.com:", "").strip().strip("/")
        if cleaned_name.endswith(".git"):
            cleaned_name = cleaned_name[:-4]
        repo_data = self.client.get_repo(cleaned_name)
        gem = self.inspect_repo(repo_data, deep=True)
        try:
            rm = self.get_readme(cleaned_name)
            if rm:
                gem["readme"] = rm
        except Exception:
            pass
        try:
            gem["ai_verdict"] = self.ai.generate_deep_verdict(gem)
        except Exception:
            pass
        return gem

    def search_forks(self, upstream_repo: str, limit: int = 8) -> List[Dict[str, Any]]:
        """First-class fork discovery: detects active, diverged forks of an upstream project."""
        cleaned_upstream = upstream_repo.replace("https://github.com/", "").strip().strip("/")
        forks_data = self.client.get_forks(cleaned_upstream, sort="newest", per_page=min(30, limit * 2))

        analyzed_forks = []
        for f in forks_data[:limit]:
            try:
                fork_gem = self.inspect_repo(f, deep=False)
                # Try to get comparison telemetry if compare_commits is available
                try:
                    comp = self.client.compare_commits(cleaned_upstream, "HEAD", f.get("full_name"))
                    fork_gem["ahead_by"] = comp.get("ahead_by", 0)
                    fork_gem["behind_by"] = comp.get("behind_by", 0)
                except Exception:
                    fork_gem["ahead_by"] = f.get("ahead_by", 0)
                    fork_gem["behind_by"] = f.get("behind_by", 0)

                # Classify relationship
                if fork_gem.get("ahead_by", 0) > 0:
                    fork_gem["fork_status"] = f"⚡ Diverged (+{fork_gem['ahead_by']} commits ahead)"
                elif fork_gem.get("pushed_days", 999) <= 14:
                    fork_gem["fork_status"] = "⚡ Active Maintained Fork"
                elif fork_gem.get("stars", 0) > 5:
                    fork_gem["fork_status"] = "🌟 Popular Divergence"
                else:
                    fork_gem["fork_status"] = "📦 Independent Fork"
                analyzed_forks.append(fork_gem)
            except Exception:
                pass

        analyzed_forks.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return analyzed_forks

    def author_gems(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Discovers hidden gems built by a specific creator without scraping private data."""
        clean_user = username.strip().lstrip("@")
        q = f"user:{clean_user} fork:false archived:false stars:1..30"
        res = self.client.search_repositories(q, sort="stars", order="desc", per_page=limit)
        items = res.get("items", [])
        return [self.inspect_repo(i, deep=True) for i in items]

    def compare_repos(self, repo1: str, repo2: str) -> Dict[str, Any]:
        """Performs an objective side-by-side trade-off analysis between two repositories."""
        g1 = self.xray_repo(repo1)
        g2 = self.xray_repo(repo2)
        score1 = g1.get("overall_score", 0)
        score2 = g2.get("overall_score", 0)
        if score1 > score2:
            winner = g1.get("full_name", repo1)
        elif score2 > score1:
            winner = g2.get("full_name", repo2)
        else:
            winner = "Tied"

        return {
            "repo1": g1,
            "repo2": g2,
            "winner": winner,
            "analyzed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

    def get_readme(self, full_name: str) -> Optional[str]:
        """Fetches the repository README content if available."""
        return self.client.get_readme(full_name)

    def get_tree_structure(self, full_name: str, max_items: int = 40) -> List[Dict[str, Any]]:
        """Fetches and structures the repository file hierarchy."""
        tree = self.client.get_tree(full_name)
        if not tree:
            return []
        items = []
        for entry in tree[:max_items]:
            path = entry.get("path", "")
            type_ = entry.get("type", "blob")
            size = entry.get("size", 0)
            items.append({
                "path": path,
                "type": type_,
                "size": size,
            })
        return items

    def get_recent_commits(self, full_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches recent commits with semantic messages and author metadata."""
        raw_commits = self.client.get_commits(full_name, per_page=limit)
        results = []
        for c in raw_commits[:limit]:
            sha = c.get("sha", "")[:7]
            commit_info = c.get("commit", {})
            author_info = commit_info.get("author", {})
            msg = commit_info.get("message", "").split("\n")[0]
            date_str = author_info.get("date", "")
            results.append({
                "sha": sha,
                "message": msg,
                "author": author_info.get("name") or (c.get("author") or {}).get("login", "unknown"),
                "date": date_str,
            })
        return results

    def search_velocity(self, language: str = "", limit: int = 8) -> List[Dict[str, Any]]:
        """Finds emerging underground repos with high commit momentum in the last 7 days."""
        now = datetime.now(timezone.utc)
        since_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        q = f"stars:2..15 pushed:>{since_date} fork:false archived:false"
        if language:
            q += f" language:{language}"
        res = self.client.search_repositories(q, sort="updated", order="desc", per_page=limit)
        items = res.get("items", [])
        return [self.inspect_repo(i, deep=True) for i in items]

    def get_commit_cadence(self, full_name: str) -> Optional[Dict[str, Any]]:
        """52-week craftsmanship rhythm: totals, gradient sparkline data & momentum verdict."""
        activity = self.client.get_commit_activity(full_name)
        if not activity:
            return None
        try:
            weeks = sorted(activity, key=lambda w: w.get("week", 0))
            totals = [max(0, int(w.get("total", 0) or 0)) for w in weeks]
            return cadence_summary(totals)
        except Exception:
            return None


def cadence_summary(weekly_totals: List[int]) -> Optional[Dict[str, Any]]:
    """Pure analyzer: converts 52 weekly commit totals into a cadence verdict."""
    if not weekly_totals:
        return None
    totals = list(weekly_totals)[-52:]
    total = sum(totals)
    if total == 0:
        return None

    best_week = max(totals)
    last4 = totals[-4:]
    prev12 = totals[-16:-4] if len(totals) >= 16 else totals[:-4]
    avg4 = sum(last4) / len(last4)
    avg_prev = (sum(prev12) / len(prev12)) if prev12 else 0.0

    if avg_prev == 0:
        ratio = 1.6 if avg4 > 0.5 else 1.0
    else:
        ratio = avg4 / avg_prev

    if ratio >= 1.5 and avg4 >= 1:
        momentum = "🚀 surging"
    elif ratio >= 1.15:
        momentum = "▲ accelerating"
    elif ratio >= 0.85:
        momentum = "▪ steady"
    else:
        momentum = "▼ cooling"

    return {
        "weeks": totals,
        "total": total,
        "best_week": best_week,
        "avg4": avg4,
        "ratio": round(ratio, 2),
        "momentum": momentum,
    }

