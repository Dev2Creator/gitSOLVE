# gitSOLVE ✦ Config Manager
import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "github_token": "",
    "theme": "warm_earth",
    "icons_mode": "auto",
    "default_language": "",
    "min_stars": 1,
    "max_stars": 10,
    "min_age_days": 60,
    "max_pushed_days": 30,
    "scans_completed": 0,
    "gems_discovered": 0,
}

def get_config_dir() -> Path:
    if "GITSOLVE_CONFIG_DIR" in os.environ:
        p = Path(os.environ["GITSOLVE_CONFIG_DIR"])
        p.mkdir(parents=True, exist_ok=True)
        return p
    default_dir = Path.home() / ".config" / "gitsolve"
    try:
        default_dir.mkdir(parents=True, exist_ok=True)
        # Test writeability
        test_file = default_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return default_dir
    except (OSError, PermissionError):
        # Fallback to local workspace or tmp directory
        fallback = Path.cwd() / ".gitsolve"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except Exception:
            tmp_fallback = Path("/tmp") / ".gitsolve"
            tmp_fallback.mkdir(parents=True, exist_ok=True)
            return tmp_fallback

def get_config_file() -> Path:
    return get_config_dir() / "config.json"

def ensure_config_dir() -> Path:
    return get_config_dir()

def load_config() -> Dict[str, Any]:
    cfg_file = get_config_file()
    if not cfg_file.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]) -> None:
    cfg_file = get_config_file()
    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception:
        pass

def update_config_value(key: str, value: Any) -> Dict[str, Any]:
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    return cfg
