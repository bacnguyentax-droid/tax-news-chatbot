"""
Configuration management for VPDT Automation Manager
"""

import os
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent
CONFIG_FILE = BASE_DIR / "config.json"
SESSION_FILE = BASE_DIR / "session_state.json"
SCREENSHOT_PATH = BASE_DIR / "dashboard_screenshot.png"

# Default Endpoints
BASE_URL = "http://vpdt.cucthue.hochiminhcity.gov.vn"
LOGIN_URL = f"{BASE_URL}/web/guest/login"

DEFAULT_CONFIG = {
    "login_url": LOGIN_URL,
    "base_url": BASE_URL,
    "username": "",
    "password": "",
    "headless": False,
    "browser_slow_mo_ms": 300,
    "default_timeout_ms": 30000,
    "save_session": True,
    "rules": []
}


def load_config() -> dict:
    """Load configuration from config.json, or create default if not exists."""
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[WARN] Error reading config file: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict) -> None:
    """Save configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_credentials() -> tuple[str, str]:
    """Retrieve stored username and password."""
    cfg = load_config()
    return cfg.get("username", ""), cfg.get("password", "")


def set_credentials(username: str, password: str) -> None:
    """Store username and password into config."""
    cfg = load_config()
    cfg["username"] = username.strip()
    cfg["password"] = password.strip()
    save_config(cfg)
