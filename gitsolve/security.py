# gitSOLVE ✦ Security & Untrusted Content Sanitizer
# Software for Humans. Never trust remote data blindly.

import re
import unicodedata
from typing import Any, Dict, List, Optional

# Regex to strip ANSI escape sequences from remote text (protects terminal from escape injection)
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Dangerous control characters (excluding standard whitespace \n, \t, \r)
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]")

# GitHub repo full_name regex: owner/repo (alphanumeric, -, _, .)
REPO_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")

def sanitize_text(text: Optional[str], max_length: int = 2000, allow_newlines: bool = True) -> str:
    """Sanitizes remote untrusted strings to prevent terminal injection or buffer overflows."""
    if not text:
        return ""
    # Strip ANSI escape codes
    clean = ANSI_ESCAPE_RE.sub("", str(text))
    # Normalize unicode to NFKC
    clean = unicodedata.normalize("NFKC", clean)
    # Strip non-printable control characters
    clean = CONTROL_CHARS_RE.sub("", clean)
    if not allow_newlines:
        clean = re.sub(r"[\r\n]+", " ", clean)
    # Truncate defensively
    if len(clean) > max_length:
        clean = clean[:max_length - 3] + "..."
    return clean.strip()

def sanitize_terminal_output(text: Optional[str], max_length: int = 2000, allow_newlines: bool = True) -> str:
    """Alias for sanitize_text for terminal display security."""
    return sanitize_text(text, max_length=max_length, allow_newlines=allow_newlines)

def sanitize_repo_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively or selectively sanitizes remote repository metadata."""
    sanitized = data.copy()
    for key in ("name", "full_name", "description", "language", "default_branch"):
        if key in sanitized and isinstance(sanitized[key], str):
            sanitized[key] = sanitize_text(sanitized[key], max_length=500)
    return sanitized

def sanitize_repo_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Alias for sanitize_repo_data."""
    return sanitize_repo_data(data)

def validate_repo_full_name(name: str) -> bool:
    """Validates that a repository identifier matches standard owner/repo format."""
    if not name or len(name) > 100:
        return False
    if ".." in name or ";" in name or "&" in name:
        return False
    return bool(REPO_NAME_RE.match(name.strip()))
