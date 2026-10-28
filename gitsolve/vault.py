# gitSOLVE ✦ The 'I Was Here First' Vault Engine
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gitsolve.config import get_config_dir, load_config, update_config_value
from gitsolve.github import GitHubClient

def get_vault_db_path() -> Path:
    return get_config_dir() / "vault.db"

def _init_vault_db() -> None:
    db_path = get_vault_db_path()
    with sqlite3.connect(db_path) as conn:
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
                sleeper_score INTEGER DEFAULT 80,
                primary_language TEXT,
                html_url TEXT,
                notes TEXT
            )
        """)
        conn.commit()

class Vault:
    def __init__(self):
        _init_vault_db()

    def save_gem(self, gem: Dict[str, Any], notes: str = "") -> bool:
        full_name = gem.get("full_name")
        if not full_name:
            return False
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        stars = gem.get("stars", 0)
        try:
            with sqlite3.connect(get_vault_db_path()) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO vault (
                        full_name, author, description, discovered_stars,
                        discovered_at, last_checked_stars, last_checked_at,
                        sleeper_score, primary_language, html_url, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    full_name,
                    gem.get("author", full_name.split("/")[0]),
                    gem.get("description", ""),
                    stars,
                    now_str,
                    stars,
                    now_str,
                    gem.get("sleeper_score", 85),
                    gem.get("primary_language", "Code"),
                    gem.get("html_url", f"https://github.com/{full_name}"),
                    notes,
                ))
                conn.commit()
            # Update discovery stats
            count = self.count()
            update_config_value("gems_discovered", count)
            return True
        except Exception:
            return False

    def remove_gem(self, full_name: str) -> bool:
        try:
            with sqlite3.connect(get_vault_db_path()) as conn:
                conn.execute("DELETE FROM vault WHERE full_name = ?", (full_name,))
                conn.commit()
            count = self.count()
            update_config_value("gems_discovered", count)
            return True
        except Exception:
            return False

    def list_gems(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(get_vault_db_path()) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vault ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def count(self) -> int:
        with sqlite3.connect(get_vault_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vault")
            res = cursor.fetchone()
            return res[0] if res else 0

    def refresh_vault(self, client: Optional[GitHubClient] = None) -> List[Dict[str, Any]]:
        """Queries GitHub for current stars and computes delta gains."""
        gh = client or GitHubClient()
        gems = self.list_gems()
        updated_gems = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        for gem in gems:
            full_name = gem["full_name"]
            try:
                repo_data = gh.get_repo(full_name)
                current_stars = repo_data.get("stargazers_count", gem["last_checked_stars"])
                delta = current_stars - gem["discovered_stars"]
                with sqlite3.connect(get_vault_db_path()) as conn:
                    conn.execute("""
                        UPDATE vault SET last_checked_stars = ?, last_checked_at = ? WHERE full_name = ?
                    """, (current_stars, now_str, full_name))
                    conn.commit()
                gem_copy = dict(gem)
                gem_copy["current_stars"] = current_stars
                gem_copy["delta_stars"] = delta
                updated_gems.append(gem_copy)
            except Exception:
                gem_copy = dict(gem)
                gem_copy["current_stars"] = gem["last_checked_stars"]
                gem_copy["delta_stars"] = gem["last_checked_stars"] - gem["discovered_stars"]
                updated_gems.append(gem_copy)

        return updated_gems

    def get_curator_rank(self) -> Tuple[str, str]:
        cnt = self.count()
        if cnt == 0:
            return "Curious Wanderer", "Save your first sleeper to start your portfolio."
        elif cnt <= 4:
            return "Underground Scout 🔍", "You have an eye for early alpha."
        elif cnt <= 12:
            return "Alpha Hunter ⚡", "Spotting masterpieces way before Twitter/X."
        elif cnt <= 25:
            return "High Tastemaker 💎", "Elite radar. Your portfolio has serious signal."
        else:
            return "Legendary Curator 👑", "Mythic status. The open-source underground answers to you."

    def export_markdown(self, filepath: Path) -> str:
        gems = self.list_gems()
        rank, desc = self.get_curator_rank()
        lines = [
            "# ✦ gitSOLVE Curator Portfolio ✦",
            "",
            f"**Curator Rank:** {rank}  ",
            f"**Total Underground Gems Saved:** {len(gems)}  ",
            f"**Exported At:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
            "",
            "| Repository | Discovered ⭐ | Current ⭐ | Delta | Language | Link |",
            "|---|---|---|---|---|---|",
        ]
        for g in gems:
            delta = g['last_checked_stars'] - g['discovered_stars']
            delta_str = f"+{delta}" if delta >= 0 else str(delta)
            lines.append(
                f"| **`{g['full_name']}`** | {g['discovered_stars']} | {g['last_checked_stars']} | **{delta_str}** | {g['primary_language']} | [GitHub]({g['html_url']}) |"
            )
        lines.append("")
        lines.append("*Generated with [gitSOLVE](https://github.com/Dev2Creator/gitSOLVE) — Underground Code. Zero Hype.*")
        
        content = "\n".join(lines)
        filepath.write_text(content, encoding="utf-8")
        return content
