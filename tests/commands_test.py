"""Tests for CLI commands."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from dailybot_cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestVersionAndHelp:

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "dailybot" in result.output
        assert "0.1.0" in result.output

    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "auth" in result.output
        assert "update" in result.output
        assert "status" in result.output
        assert "agent" in result.output
        assert "--api-url" in result.output

    @patch("dailybot_cli.main.set_api_url_override")
    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_api_url_override(
        self,
        mock_client_cls: MagicMock,
        mock_get_token: MagicMock,
        mock_set_override: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.return_value = {
            "followups_count": 1,
            "attached_followups": [{"followup_name": "Standup", "action": "created"}],
        }

        result = runner.invoke(cli, ["--api-url", "https://staging.dailybot.com", "update", "test"])
        assert result.exit_code == 0
        mock_set_override.assert_called_once_with("https://staging.dailybot.com")


class TestAuthCommands:

    def test_auth_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["auth", "--help"])
        assert result.exit_code == 0
        assert "login" in result.output
        assert "logout" in result.output
        assert "status" in result.output

    @patch("dailybot_cli.commands.auth.DailyBotClient")
    @patch("dailybot_cli.commands.auth.save_credentials")
    def test_auth_login_success(
        self,
        mock_save: MagicMock,
        mock_client_cls: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.api_url = "https://api.dailybot.com"
        mock_client.request_code.return_value = {"detail": "Code sent"}
        mock_client.verify_code.return_value = {
            "token": "tok123",
            "organization": "MyOrg",
            "organization_id": 1,
        }

        result = runner.invoke(cli, ["auth", "login"], input="user@test.com\n123456\n")
        assert result.exit_code == 0
        assert "Logged in" in result.output
        mock_save.assert_called_once()

    @patch("dailybot_cli.commands.auth.DailyBotClient")
    def test_auth_login_bad_email(
        self, mock_client_cls: MagicMock, runner: CliRunner
    ) -> None:
        from dailybot_cli.api_client import APIError

        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.request_code.side_effect = APIError(400, "No account found")

        result = runner.invoke(cli, ["auth", "login"], input="bad@test.com\n")
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.auth.load_credentials")
    @patch("dailybot_cli.commands.auth.DailyBotClient")
    def test_auth_status_success(
        self,
        mock_client_cls: MagicMock,
        mock_load: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_load.return_value = {"token": "tok", "email": "u@t.com"}
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.auth_status.return_value = {
            "email": "u@t.com",
            "organization": "Org",
            "expires_at": "2026-05-01",
        }

        result = runner.invoke(cli, ["auth", "status"])
        assert result.exit_code == 0
        assert "u@t.com" in result.output

    @patch("dailybot_cli.commands.auth.get_token")
    @patch("dailybot_cli.commands.auth.clear_credentials")
    @patch("dailybot_cli.commands.auth.DailyBotClient")
    def test_auth_logout(
        self,
        mock_client_cls: MagicMock,
        mock_clear: MagicMock,
        mock_get_token: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.logout.return_value = {}

        result = runner.invoke(cli, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_clear.assert_called_once()


class TestUpdateCommand:

    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_message(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.return_value = {
            "followups_count": 1,
            "attached_followups": [{"followup_name": "Standup"}],
        }

        result = runner.invoke(cli, ["update", "Finished auth module"])
        assert result.exit_code == 0
        assert "1 check-in" in result.output

    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_structured(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.return_value = {
            "followups_count": 1,
            "attached_followups": [{"followup_name": "Standup"}],
        }

        result = runner.invoke(
            cli, ["update", "--done", "Auth", "--doing", "Tests", "--blocked", "None"]
        )
        assert result.exit_code == 0
        mock_client.submit_update.assert_called_once_with(
            message=None, done="Auth", doing="Tests", blocked="None"
        )

    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_shows_submitted_for_created(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.return_value = {
            "followups_count": 1,
            "attached_followups": [{"followup_name": "Standup", "action": "created"}],
        }

        result = runner.invoke(cli, ["update", "Did some work"])
        assert result.exit_code == 0
        assert "Submitted" in result.output

    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_shows_updated_for_enriched(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.return_value = {
            "followups_count": 1,
            "attached_followups": [{"followup_name": "Standup", "action": "updated"}],
        }

        result = runner.invoke(cli, ["update", "More progress"])
        assert result.exit_code == 0
        assert "Updated" in result.output

    @patch("dailybot_cli.commands.update.get_token")
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_ai_processing_failed(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        from dailybot_cli.api_client import APIError

        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.side_effect = APIError(400, "AI processing failed for input")

        result = runner.invoke(cli, ["update", "???"])
        assert result.exit_code != 0
        assert "could not process" in result.output
        assert "support@dailybot.com" in result.output

    @patch("dailybot_cli.commands.update.get_token")
    def test_update_not_logged_in(
        self, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = None
        result = runner.invoke(cli, ["update", "test"])
        assert result.exit_code != 0


class TestStatusCommand:

    @patch("dailybot_cli.commands.status.get_token")
    @patch("dailybot_cli.commands.status.DailyBotClient")
    def test_status_with_checkins(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.get_status.return_value = {
            "count": 1,
            "pending_checkins": [
                {
                    "followup_name": "Daily Standup",
                    "template_questions": [
                        {"question": "What did you do?", "is_blocker": False},
                    ],
                }
            ],
        }

        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Daily Standup" in result.output

    @patch("dailybot_cli.commands.status.get_token")
    @patch("dailybot_cli.commands.status.DailyBotClient")
    def test_status_no_checkins(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.get_status.return_value = {"count": 0, "pending_checkins": []}

        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "No pending" in result.output


class TestAgentCommand:

    @patch("dailybot_cli.commands.agent.get_api_key")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_update(
        self, mock_client_cls: MagicMock, mock_get_key: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_key.return_value = "apikey123"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_agent_report.return_value = {"id": 1, "uuid": "abc"}

        result = runner.invoke(
            cli, ["agent", "update", "Deployed v2.1", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "Report submitted" in result.output

    @patch("dailybot_cli.commands.agent.get_api_key")
    def test_agent_update_no_api_key(
        self, mock_get_key: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_key.return_value = None
        result = runner.invoke(cli, ["agent", "update", "test"])
        assert result.exit_code != 0
