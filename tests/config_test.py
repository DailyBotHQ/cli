"""Tests for config module."""

import json
import os
from pathlib import Path
from typing import Any, Optional
from unittest import mock

import pytest

from dailybot_cli.config import (
    clear_credentials,
    get_api_key,
    get_api_url,
    get_token,
    load_credentials,
    save_credentials,
)


@pytest.fixture
def tmp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override config paths to use a temp directory."""
    config_dir: Path = tmp_path / ".config" / "dailybot"
    creds_file: Path = config_dir / "credentials.json"
    monkeypatch.setattr("dailybot_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("dailybot_cli.config.CREDENTIALS_FILE", creds_file)
    return config_dir


def test_save_and_load_credentials(tmp_config: Path) -> None:
    save_credentials(
        token="tok123",
        email="user@example.com",
        organization="MyOrg",
        organization_uuid="org-uuid-42",
    )
    creds: Optional[dict[str, Any]] = load_credentials()
    assert creds is not None
    assert creds["token"] == "tok123"
    assert creds["email"] == "user@example.com"
    assert creds["organization"] == "MyOrg"
    assert creds["organization_uuid"] == "org-uuid-42"


def test_load_credentials_no_file(tmp_config: Path) -> None:
    assert load_credentials() is None


def test_clear_credentials(tmp_config: Path) -> None:
    save_credentials(token="t", email="e", organization="o", organization_uuid="uuid-1")
    clear_credentials()
    assert load_credentials() is None


def test_get_api_url_default(tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DAILYBOT_API_URL", raising=False)
    assert get_api_url() == "https://api.dailybot.com"


def test_get_api_url_from_env(tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILYBOT_API_URL", "http://localhost:8600/")
    assert get_api_url() == "http://localhost:8600"


def test_get_token_from_env(tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILYBOT_CLI_TOKEN", "env_token")
    assert get_token() == "env_token"


def test_get_token_from_credentials(tmp_config: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DAILYBOT_CLI_TOKEN", raising=False)
    save_credentials(token="file_token", email="e", organization="o", organization_uuid="uuid-1")
    assert get_token() == "file_token"


def test_get_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILYBOT_API_KEY", "apikey123")
    assert get_api_key() == "apikey123"


def test_get_api_key_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DAILYBOT_API_KEY", raising=False)
    assert get_api_key() is None


def test_credentials_file_permissions(tmp_config: Path) -> None:
    save_credentials(token="t", email="e", organization="o", organization_uuid="uuid-1")
    creds_file: Path = tmp_config / "credentials.json"
    mode: int = os.stat(creds_file).st_mode & 0o777
    assert mode == 0o600
