"""Credential and configuration management for DailyBot CLI."""

import json
import os
from pathlib import Path
from typing import Any, Optional


DEFAULT_API_URL: str = "https://api.dailybot.com"
_api_url_override: Optional[str] = None


def set_api_url_override(url: str) -> None:
    """Set a CLI-level API URL override (from --api-url flag)."""
    global _api_url_override
    _api_url_override = url.rstrip("/")
CONFIG_DIR: Path = Path.home() / ".config" / "dailybot"
CREDENTIALS_FILE: Path = CONFIG_DIR / "credentials.json"


def get_config_dir() -> Path:
    """Return the config directory, creating it if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_credentials() -> Optional[dict[str, Any]]:
    """Load stored credentials from disk."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(CREDENTIALS_FILE.read_text())
        return data if data.get("token") else None
    except (json.JSONDecodeError, KeyError):
        return None


def save_credentials(
    token: str,
    email: str,
    organization: str,
    organization_id: int,
    api_url: str = DEFAULT_API_URL,
) -> None:
    """Save credentials to disk."""
    get_config_dir()
    CREDENTIALS_FILE.write_text(
        json.dumps(
            {
                "token": token,
                "email": email,
                "organization": organization,
                "organization_id": organization_id,
                "api_url": api_url,
            },
            indent=2,
        )
    )
    # Restrict file permissions (owner read/write only)
    os.chmod(CREDENTIALS_FILE, 0o600)


def clear_credentials() -> None:
    """Remove stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def get_api_url() -> str:
    """Return the API URL (--api-url flag > env var > credentials > default)."""
    if _api_url_override:
        return _api_url_override
    env_url: Optional[str] = os.environ.get("DAILYBOT_API_URL")
    if env_url:
        return env_url.rstrip("/")
    creds: Optional[dict[str, Any]] = load_credentials()
    if creds and creds.get("api_url"):
        return str(creds["api_url"]).rstrip("/")
    return DEFAULT_API_URL


def get_token() -> Optional[str]:
    """Return the stored auth token, or the DAILYBOT_CLI_TOKEN env var."""
    env_token: Optional[str] = os.environ.get("DAILYBOT_CLI_TOKEN")
    if env_token:
        return env_token
    creds: Optional[dict[str, Any]] = load_credentials()
    if creds:
        return creds.get("token")
    return None


def get_api_key() -> Optional[str]:
    """Return the org API key from environment (for agent mode)."""
    return os.environ.get("DAILYBOT_API_KEY")
