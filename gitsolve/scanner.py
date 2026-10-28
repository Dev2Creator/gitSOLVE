# gitSOLVE ✦ 4-Stage Deep X-Ray Code Inspection Engine
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from gitsolve.config import load_config
from gitsolve.github import GitHubClient

class RepoInspector:
    def __init__(self, client: Optional[GitHubClient] = None):
        self.client = client or GitHubClient()

    def inspect_repo(self, repo_data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Runs the 4-stage forensic diagnostic on a candidate repo."""
        full_name = repo_data.get("full_name", "")
        stars = repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks_count", 0)
        open_issues = repo_data.get("open_issues_count", 0)
        created_at_str = repo_data.get("created_at", "")
        pushed_at_str = repo_data.get("pushed_at", "")
        description = repo_data.get("description") or ""
        primary_lang = repo_data.get("language") or "Code"
        html_url = repo_data.get("html_url", f"https://github.com/{full_name}")

        # Age calculation
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

        # Diagnostic findings accumulator
        findings: List[str] = []
        substance_score = 0
        
        has_tests = False
        has_ci = False
        has_demo = False
        modern_manifest = None
        loc_estimate = 0
        commit_spread_days = 0
        semantic_commit_count = 0

        # STAGE 1: Tree & Substance Audit
        tree = self.client.get_tree(full_name) if deep else []
        if tree:
            manifests = {
                "Cargo.toml": "Rust/Cargo",
                "pyproject.toml": "Modern Python",
                "go.mod": "Go Module",
                "package.json": "TypeScript/Node",
                "CMakeLists.txt": "C/C++ Modern CMake",
                "Makefile": "Makefile",
                "Dockerfile": "Containerized",
                "flake.nix": "Nix Flake",
            }
            code_files = 0
            for item in tree:
                path = item.get("path", "")
                p_lower = path.lower()

                # Detect manifests
                for m_file, m_label in manifests.items():
                    if path == m_file or path.endswith("/" + m_file):
                        if not modern_manifest:
                            modern_manifest = m_label

                # Detect tests
                if any(t_dir in p_lower for t_dir in ["test/", "tests/", "spec/", "benches/", "_test.go", ".test.ts", ".spec.ts", "test_"]):
                    has_tests = True

                # Detect CI/CD
                if ".github/workflows" in path or ".gitlab-ci.yml" in path:
                    has_ci = True

                # Count real source files (excluding vendor/lockfiles)
                if not any(v in p_lower for v in ["node_modules", "vendor/", "dist/", "target/", ".git/"]):
                    if any(p_lower.endswith(ext) for ext in [".rs", ".py", ".go", ".ts", ".tsx", ".c", ".cpp", ".h", ".zig", ".lua", ".swift", ".kt"]):
                        code_files += 1

            if code_files > 0:
                loc_estimate = code_files * 85  # Rough heuristic
                if code_files >= 15:
                    findings.append(f"Substantial architecture: ~{code_files} handwritten source modules (~{loc_estimate:,} LoC)")
                    substance_score += 20
                elif code_files >= 5:
                    findings.append(f"Compact handcrafted codebase (~{code_files} modules)")
                    substance_score += 15
                else:
                    substance_score += 10
            else:
                substance_score += 5

            if modern_manifest:
                findings.append(f"Clean build manifest: configured with {modern_manifest}")
                substance_score += 15

            if has_tests:
                findings.append("Dedicated test suite & verification harness present")
                substance_score += 15

            if has_ci:
                findings.append("Automated GitHub Actions CI/CD workflows configured")
                substance_score += 10
        else:
            # Fallback if tree was skipped or inaccessible
            substance_score += 25

        # STAGE 2: Commit Forensics
        commits = self.client.get_commits(full_name, per_page=15) if deep else []
        if commits:
            semantic_regex = re.compile(r"^(feat|fix|perf|refactor|docs|test|chore|style|build|ci)(\([a-zA-Z0-9_-]+\))?:", re.IGNORECASE)
            commit_dates = []
            for c in commits:
                commit_obj = c.get("commit", {})
                msg = commit_obj.get("message", "").strip().split("\n")[0]
                if semantic_regex.match(msg):
                    semantic_commit_count += 1
                author_date_str = commit_obj.get("author", {}).get("date")
                if author_date_str:
                    try:
                        commit_dates.append(datetime.fromisoformat(author_date_str.replace("Z", "+00:00")))
                    except Exception:
                        pass

            if len(commit_dates) >= 2:
                commit_dates.sort()
                commit_spread_days = (commit_dates[-1] - commit_dates[0]).days

            if semantic_commit_count >= 5:
                findings.append(f"Disciplined commit hygiene: {semantic_commit_count}/15 commits use strict semantic conventions")
                substance_score += 12
            elif semantic_commit_count >= 2:
                substance_score += 6

            if commit_spread_days >= 14:
                findings.append(f"Consistent dev cadence: active development spanning multiple weeks")
                substance_score += 8
            else:
                substance_score += 4
        else:
            substance_score += 10

        # STAGE 3: Proof of Life & Documentation Audit
        readme = self.client.get_readme(full_name) if deep else None
        if readme:
            readme_len = len(readme)
            has_code_blocks = "```" in readme
            has_images = any(ext in readme.lower() for ext in [".gif", ".png", ".svg", ".jpg", "asciinema"])
            has_install = any(k in readme.lower() for k in ["install", "usage", "quickstart", "getting started", "setup"])

            if has_images:
                has_demo = True
                findings.append("Proof of life: includes visual diagrams or live demo assets")
                substance_score += 8

            if has_code_blocks and has_install:
                findings.append("Complete documentation: clean code examples and setup guide")
                substance_score += 12
            elif readme_len > 800:
                substance_score += 8
            elif readme_len > 300:
                substance_score += 5
        else:
            substance_score += 4

        # STAGE 4: Sleeper Index Calculation
        # Formula: (Substance / (Stars + 1)) * 12 clamped to 100
        raw_sleeper = int((substance_score / (stars + 1)) * 12)
        sleeper_score = max(45, min(99, raw_sleeper))

        # License
        license_name = repo_data.get("license", {}).get("name") if isinstance(repo_data.get("license"), dict) else None

        return {
            "full_name": full_name,
            "name": repo_data.get("name", ""),
            "author": full_name.split("/")[0] if "/" in full_name else "",
            "stars": stars,
            "forks": forks,
            "open_issues": open_issues,
            "description": description,
            "primary_language": primary_lang,
            "html_url": html_url,
            "age_text": age_text,
            "pushed_days": pushed_days,
            "sleeper_score": sleeper_score,
            "substance_score": substance_score,
            "findings": findings,
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_demo": has_demo,
            "license": license_name,
            "loc_estimate": loc_estimate,
        }

    def search_radar(
        self,
        topic: str = "",
        language: str = "",
        query_text: str = "",
        min_stars: int = 1,
        max_stars: int = 10,
        min_age_days: int = 60,
        max_pushed_days: int = 30,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Precision underground radar query."""
        now = datetime.now(timezone.utc)
        created_before = (now - timedelta(days=min_age_days)).strftime("%Y-%m-%d")
        pushed_after = (now - timedelta(days=max_pushed_days)).strftime("%Y-%m-%d")

        q_parts = [
            f"stars:{min_stars}..{max_stars}",
            f"created:<={created_before}",
            f"pushed:>={pushed_after}",
            "fork:false",
            "archived:false",
            "size:>100",
        ]
        if topic:
            q_parts.append(f"topic:{topic.strip()}")
        if language:
            q_parts.append(f"language:{language.strip()}")
        if query_text:
            q_parts.append(query_text.strip())

        full_query = " ".join(q_parts)
        res = self.client.search_repositories(full_query, sort="updated", order="desc", per_page=min(20, limit * 2))
        items = res.get("items", [])

        gems = []
        for item in items[:limit]:
            try:
                gem = self.inspect_repo(item, deep=True)
                gems.append(gem)
            except Exception:
                # If inspection of one item failed, still return basic representation
                gems.append(self.inspect_repo(item, deep=False))

        # Rank by sleeper score descending
        gems.sort(key=lambda g: g.get("sleeper_score", 0), reverse=True)
        return gems

    def search_fresh(self, language: str = "", limit: int = 8) -> List[Dict[str, Any]]:
        """Stream repos updated in the last 24-48 hours that are at least 2 months old."""
        return self.search_radar(
            language=language,
            min_age_days=60,
            max_pushed_days=2,
            min_stars=1,
            max_stars=8,
            limit=limit,
        )

    def xray_repo(self, full_name: str) -> Dict[str, Any]:
        """Deep forensic inspection on a specific repo."""
        cleaned_name = full_name.replace("https://github.com/", "").strip().strip("/")
        repo_data = self.client.get_repo(cleaned_name)
        return self.inspect_repo(repo_data, deep=True)

    def author_gems(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find hidden gems built by a specific author."""
        q = f"user:{username.strip()} fork:false archived:false stars:1..15"
        res = self.client.search_repositories(q, sort="stars", order="desc", per_page=limit)
        items = res.get("items", [])
        return [self.inspect_repo(i, deep=True) for i in items]
