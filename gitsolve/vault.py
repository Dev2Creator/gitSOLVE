# gitSOLVE ✦ Robust Vault & Seen Tracker Engine
# Software for Humans. Persistent discoveries with safe schema migrations.

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gitsolve.config import get_config_dir, load_config, update_config_value
from gitsolve.github import GitHubClient

def get_vault_db_path() -> Path:
    return get_config_dir() / "vault.db"

from contextlib import contextmanager

@contextmanager
def _get_connection(db_path: Path):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

def _init_vault_db(db_path: Optional[Path] = None) -> None:
    target_path = db_path or get_vault_db_path()
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with _get_connection(target_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vault (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT UNIQUE NOT NULL,
                    author TEXT NOT NULL,
                    description TEXT,
                    discovered_stars INTEGER NOT NULL,
                    discovered_at TEXT NOT NULL,
                    last_checked_stars INTEGER NOT NULL,
                    last_checked_at TEXT,
                    health_score INTEGER DEFAULT 75,
                    discovery_score INTEGER DEFAULT 85,
                    overall_score INTEGER DEFAULT 80,
                    primary_language TEXT,
                    html_url TEXT,
                    notes TEXT DEFAULT '',
                    tags TEXT DEFAULT '',
                    review_status TEXT DEFAULT 'unreviewed'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seen_repos (
                    full_name TEXT PRIMARY KEY,
                    first_seen_at TEXT,
                    last_seen_at TEXT,
                    seen_count INTEGER DEFAULT 1,
                    source TEXT DEFAULT 'radar'
                )
            """)
            # Migration check: add columns if an older database existed
            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA table_info(vault)")
                existing_cols = [row[1] for row in cursor.fetchall()]
                if "tags" not in existing_cols:
                    try:
                        conn.execute("ALTER TABLE vault ADD COLUMN tags TEXT DEFAULT ''")
                    except Exception:
                        pass
                if "review_status" not in existing_cols:
                    try:
                        conn.execute("ALTER TABLE vault ADD COLUMN review_status TEXT DEFAULT 'unreviewed'")
                    except Exception:
                        pass
                if "health_score" not in existing_cols:
                    try:
                        conn.execute("ALTER TABLE vault ADD COLUMN health_score INTEGER DEFAULT 75")
                    except Exception:
                        pass
                if "discovery_score" not in existing_cols:
                    try:
                        conn.execute("ALTER TABLE vault ADD COLUMN discovery_score INTEGER DEFAULT 85")
                    except Exception:
                        pass
                cursor.execute("PRAGMA table_info(seen_repos)")
                seen_cols = [row[1] for row in cursor.fetchall()]
                if "source" not in seen_cols:
                    try:
                        conn.execute("ALTER TABLE seen_repos ADD COLUMN source TEXT DEFAULT 'radar'")
                    except Exception:
                        pass
                conn.commit()
            finally:
                cursor.close()
    except Exception:
        pass

class Vault:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else get_vault_db_path()
        _init_vault_db(self.db_path)

    def mark_seen(self, full_name: str, source: str = "radar") -> None:
        """Records that a repository has been presented to the user to avoid repetitive output."""
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            with _get_connection(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO seen_repos (full_name, first_seen_at, last_seen_at, seen_count, source)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(full_name) DO UPDATE SET
                        last_seen_at = excluded.last_seen_at,
                        seen_count = seen_count + 1,
                        source = excluded.source
                """, (full_name, now_str, now_str, source))
                conn.commit()
        except Exception:
            pass

    def is_seen(self, full_name: str) -> bool:
        try:
            with _get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT 1 FROM seen_repos WHERE full_name = ?", (full_name,))
                    return cursor.fetchone() is not None
                finally:
                    cursor.close()
        except Exception:
            return False

    def filter_unseen(self, candidates: List[str]) -> List[str]:
        """Filters a list of candidate repo full_names to only those not seen yet."""
        return [c for c in candidates if not self.is_seen(c)]

    def get_seen_count(self) -> int:
        try:
            with _get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM seen_repos")
                    res = cursor.fetchone()
                    return res[0] if res else 0
                finally:
                    cursor.close()
        except Exception:
            return 0

    def save_gem(
        self,
        gem: Dict[str, Any],
        notes: str = "",
        tags: Any = "",
        status: str = "saved",
    ) -> bool:
        full_name = gem.get("full_name")
        if not full_name:
            return False
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        stars = gem.get("stars", gem.get("stargazers_count", 0))
        tags_str = ", ".join(tags) if isinstance(tags, (list, tuple, set)) else str(tags or "")

        try:
            with _get_connection(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO vault (
                        full_name, author, description, discovered_stars,
                        discovered_at, last_checked_stars, last_checked_at,
                        health_score, discovery_score, overall_score,
                        primary_language, html_url, notes, tags, review_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name,
                    gem.get("author", full_name.split("/")[0]),
                    gem.get("description", ""),
                    stars,
                    now_str,
                    stars,
                    now_str,
                    gem.get("health_score", 80),
                    gem.get("discovery_score", 85),
                    gem.get("overall_score", 82),
                    gem.get("primary_language", "Code"),
                    gem.get("html_url", f"https://github.com/{full_name}"),
                    notes,
                    tags_str,
                    status,
                ))
                conn.commit()
            count = self.count()
            update_config_value("gems_discovered", count)
            return True
        except Exception:
            return False

    def update_gem(self, full_name: str, notes: Optional[str] = None, tags: Optional[str] = None, status: Optional[str] = None) -> bool:
        updates = []
        params = []
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        if status is not None:
            updates.append("review_status = ?")
            params.append(status)
        if not updates:
            return True
        params.append(full_name)
        try:
            with _get_connection(self.db_path) as conn:
                conn.execute(f"UPDATE vault SET {', '.join(updates)} WHERE full_name = ?", params)
                conn.commit()
            return True
        except Exception:
            return False

    def remove_gem(self, full_name: str) -> bool:
        try:
            with _get_connection(self.db_path) as conn:
                conn.execute("DELETE FROM vault WHERE full_name = ?", (full_name,))
                conn.commit()
            count = self.count()
            update_config_value("gems_discovered", count)
            return True
        except Exception:
            return False

    def list_gems(self, tag: str = "", status: str = "", query: str = "") -> List[Dict[str, Any]]:
        sql = "SELECT * FROM vault WHERE 1=1"
        params = []
        if tag:
            sql += " AND tags LIKE ?"
            params.append(f"%{tag}%")
        if status:
            sql += " AND review_status = ?"
            params.append(status)
        if query:
            sql += " AND (full_name LIKE ? OR description LIKE ? OR notes LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q])
        sql += " ORDER BY id DESC"

        try:
            with _get_connection(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                try:
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    results = []
                    for row in rows:
                        d = dict(row)
                        raw_tags = d.get("tags") or ""
                        d["tags"] = [t.strip() for t in raw_tags.split(",") if t.strip()]
                        results.append(d)
                    return results
                finally:
                    cursor.close()
        except Exception:
            return []

    def count(self) -> int:
        try:
            with _get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM vault")
                    res = cursor.fetchone()
                    return res[0] if res else 0
                finally:
                    cursor.close()
        except Exception:
            return 0

    def refresh_vault(self, client: Optional[GitHubClient] = None) -> List[Dict[str, Any]]:
        """Queries GitHub for current stars and flags deleted or renamed repositories."""
        gh = client or GitHubClient()
        gems = self.list_gems()
        updated_gems = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

        for gem in gems:
            full_name = gem["full_name"]
            try:
                repo_data = gh.get_repo(full_name)
                current_stars = repo_data.get("stargazers_count", gem["last_checked_stars"])
                delta = current_stars - gem["discovered_stars"]
                with _get_connection(self.db_path) as conn:
                    conn.execute("""
                        UPDATE vault SET last_checked_stars = ?, last_checked_at = ? WHERE full_name = ?
                    """, (current_stars, now_str, full_name))
                    conn.commit()
                gem_copy = dict(gem)
                gem_copy["current_stars"] = current_stars
                gem_copy["delta_stars"] = delta
                gem_copy["status_flag"] = "Active"
                updated_gems.append(gem_copy)
            except Exception as e:
                err_msg = str(e)
                status_flag = "404 Not Found" if "404" in err_msg else "Check Failed"
                gem_copy = dict(gem)
                gem_copy["current_stars"] = gem["last_checked_stars"]
                gem_copy["delta_stars"] = gem["last_checked_stars"] - gem["discovered_stars"]
                gem_copy["status_flag"] = status_flag
                updated_gems.append(gem_copy)

        return updated_gems

    def get_curator_rank(self) -> Tuple[str, str]:
        cnt = self.count()
        if cnt == 0:
            return "NOVICE OBSERVER", "Save your first sleeper to start your portfolio."
        elif cnt <= 4:
            return "UNDERGROUND SCOUT 🔍", "You have an eye for early alpha."
        elif cnt <= 12:
            return "CODE ARCHAEOLOGIST ⚡", "Spotting masterpieces way before Twitter/X."
        elif cnt <= 25:
            return "HIGH TASTEMAKER 💎", "Elite radar. Your portfolio has serious signal."
        else:
            return "LEGENDARY CURATOR 👑", "Mythic status. The open-source underground answers to you."

    def export_json(self, filepath: Path) -> str:
        gems = self.list_gems()
        payload = {
            "app": "gitSOLVE",
            "version": "0.1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "gems_count": len(gems),
            "gems": gems,
        }
        content = json.dumps(payload, indent=2)
        filepath.write_text(content, encoding="utf-8")
        return content

    def import_json(self, filepath: Path) -> int:
        content = filepath.read_text(encoding="utf-8")
        data = json.loads(content)
        gems = data.get("gems", [])
        imported = 0
        for g in gems:
            if self.save_gem(g, notes=g.get("notes", ""), tags=g.get("tags", []), status=g.get("review_status", "saved")):
                imported += 1
        return imported

    def export_markdown(self, filepath: Path) -> str:
        gems = self.list_gems()
        rank, desc = self.get_curator_rank()
        lines = [
            "# ✦ gitSOLVE Curator Portfolio ✦",
            "",
            f"**Curator Rank:** {rank}  ",
            f"**Total Underground Gems Saved:** {len(gems)}  ",
            f"**Exported At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
            "",
            "| Repository | Discovered ⭐ | Current ⭐ | Delta | Status | Language | Notes | Link |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for g in gems:
            delta = g['last_checked_stars'] - g['discovered_stars']
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            notes_str = g.get("notes", "") or "-"
            status_str = g.get("review_status", "unreviewed")
            tags_str = ", ".join(g.get("tags", [])) if g.get("tags") else "-"
            lines.append(
                f"| **`{g['full_name']}`** | {g['discovered_stars']} | {g['last_checked_stars']} | **{delta_str}** | {status_str} | {g['primary_language']} | {notes_str} | [GitHub]({g['html_url']}) |"
            )
        lines.append("")
        lines.append("*Generated with [gitSOLVE](https://github.com/Dev2Creator/gitSOLVE) — Underground Code. Zero Hype.*")

        content = "\n".join(lines)
        filepath.write_text(content, encoding="utf-8")
        return content
