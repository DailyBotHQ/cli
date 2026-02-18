"""Tests for CLI commands."""

from pathlib import Path
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
        assert "login" in result.output
        assert "logout" in result.output
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


class TestLoginCommand:

    @patch("dailybot_cli.commands.auth.DailyBotClient")
    @patch("dailybot_cli.commands.auth.save_credentials")
    def test_login_single_org(
        self,
        mock_save: MagicMock,
        mock_client_cls: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.api_url = "https://api.dailybot.com"
        mock_client.request_code.return_value = {
            "detail": "Verification code sent to your email.",
            "organizations": [{"id": 1, "name": "MyOrg", "uuid": "org-uuid-456"}],
            "is_multi_org": False,
        }
        mock_client.verify_code.return_value = {
            "requires_organization_selection": False,
            "token": "tok123",
            "user": {"email": "user@test.com"},
            "organization": {"id": 1, "name": "MyOrg", "uuid": "org-uuid-456"},
        }

        result = runner.invoke(cli, ["login"], input="user@test.com\n123456\n")
        assert result.exit_code == 0
        assert "Logged in" in result.output
        assert "MyOrg" in result.output
        mock_save.assert_called_once()
        # Single-org: verify is called once with organization_id
        mock_client.verify_code.assert_called_once_with("user@test.com", "123456", organization_id=1)

    @patch("dailybot_cli.commands.auth.questionary")
    @patch("dailybot_cli.commands.auth.DailyBotClient")
    @patch("dailybot_cli.commands.auth.save_credentials")
    def test_login_multi_org(
        self,
        mock_save: MagicMock,
        mock_client_cls: MagicMock,
        mock_questionary: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.api_url = "https://api.dailybot.com"
        orgs = [
            {"id": 1, "name": "Acme Corp", "uuid": "abc-123"},
            {"id": 2, "name": "Side Project", "uuid": "def-456"},
        ]
        mock_client.request_code.return_value = {
            "detail": "Verification code sent to your email.",
            "organizations": orgs,
            "is_multi_org": True,
        }
        mock_client.verify_code.return_value = {
            "requires_organization_selection": False,
            "token": "tok456",
            "user": {"email": "user@test.com"},
            "organization": {"id": 2, "name": "Side Project", "uuid": "def-456"},
        }
        # Mock questionary.select to return the second org
        mock_questionary.select.return_value.ask.return_value = orgs[1]

        # Enter email, code (org selection handled by questionary mock)
        result = runner.invoke(cli, ["login"], input="user@test.com\n123456\n")
        assert result.exit_code == 0
        assert "Logged in" in result.output
        assert "Side Project" in result.output
        # Org selected before verify — single call with org_id
        mock_client.verify_code.assert_called_once_with("user@test.com", "123456", organization_id=2)

    @patch("dailybot_cli.commands.auth.DailyBotClient")
    def test_login_bad_email(
        self, mock_client_cls: MagicMock, runner: CliRunner
    ) -> None:
        from dailybot_cli.api_client import APIError

        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.request_code.side_effect = APIError(400, "No account found")

        result = runner.invoke(cli, ["login"], input="bad@test.com\n")
        assert result.exit_code != 0


class TestLogoutCommand:

    @patch("dailybot_cli.commands.auth.get_token")
    @patch("dailybot_cli.commands.auth.clear_credentials")
    @patch("dailybot_cli.commands.auth.DailyBotClient")
    def test_logout(
        self,
        mock_client_cls: MagicMock,
        mock_clear: MagicMock,
        mock_get_token: MagicMock,
        runner: CliRunner,
    ) -> None:
        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.logout.return_value = {}

        result = runner.invoke(cli, ["logout"])
        assert result.exit_code == 0
        assert "Logged out" in result.output
        mock_clear.assert_called_once()

    @patch("dailybot_cli.commands.auth.get_token")
    def test_logout_not_logged_in(
        self, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_token.return_value = None
        result = runner.invoke(cli, ["logout"])
        assert result.exit_code == 0
        assert "Not logged in" in result.output


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
    @patch("dailybot_cli.commands.update.DailyBotClient")
    def test_update_timeout(
        self, mock_client_cls: MagicMock, mock_get_token: MagicMock, runner: CliRunner
    ) -> None:
        import httpx

        mock_get_token.return_value = "tok"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_update.side_effect = httpx.ReadTimeout("timed out")

        result = runner.invoke(cli, ["update", "test"])
        assert result.exit_code != 0
        assert "timed out" in result.output

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


class TestInteractiveLogin:

    @patch("dailybot_cli.commands.interactive.questionary")
    @patch("dailybot_cli.commands.interactive._do_login")
    @patch("dailybot_cli.commands.interactive.load_credentials")
    @patch("dailybot_cli.commands.interactive.get_token")
    def test_interactive_guides_login_when_not_authenticated(
        self,
        mock_get_token: MagicMock,
        mock_load_creds: MagicMock,
        mock_do_login: MagicMock,
        mock_questionary: MagicMock,
        runner: CliRunner,
    ) -> None:
        # First call: not logged in; second call (after _do_login): return creds
        mock_get_token.return_value = None
        mock_load_creds.side_effect = [
            None,
            {"token": "tok", "email": "u@t.com", "organization": "Org"},
        ]
        # Mock questionary.select to return "Quit"
        mock_questionary.select.return_value.ask.return_value = "Quit"
        # Provide email for the prompt (code is handled inside _do_login which is mocked)
        result = runner.invoke(cli, [], input="u@t.com\n")
        mock_do_login.assert_called_once_with("u@t.com")


class TestAgentCommand:

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_update(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_agent_report.return_value = {"id": 1, "uuid": "abc"}

        result = runner.invoke(
            cli, ["agent", "update", "Deployed v2.1", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "Report submitted" in result.output

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_agent_update_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(cli, ["agent", "update", "test"])
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_health_ok(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_agent_health.return_value = {
            "agent_name": "Claude Code",
            "status": "healthy",
            "last_check": "2025-01-01T00:00:00Z",
            "history": [],
        }

        result = runner.invoke(
            cli, ["agent", "health", "--ok", "--message", "All good", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "healthy" in result.output
        assert "Claude Code" in result.output
        mock_client.submit_agent_health.assert_called_once_with(
            agent_name="Claude Code", ok=True, message="All good"
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_health_fail(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_agent_health.return_value = {
            "agent_name": "CI Bot",
            "status": "unhealthy",
            "last_check": "2025-01-01T00:00:00Z",
            "history": [],
        }

        result = runner.invoke(
            cli, ["agent", "health", "--fail", "--message", "DB down", "--name", "CI Bot"]
        )
        assert result.exit_code == 0
        assert "unhealthy" in result.output
        assert "CI Bot" in result.output
        mock_client.submit_agent_health.assert_called_once_with(
            agent_name="CI Bot", ok=False, message="DB down"
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_health_status(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.get_agent_health.return_value = {
            "agent_name": "Claude Code",
            "status": "healthy",
            "last_check": "2025-01-01T00:00:00Z",
            "history": [
                {"timestamp": "2025-01-01T00:00:00Z", "status": "healthy", "message": "All good"},
            ],
        }

        result = runner.invoke(
            cli, ["agent", "health", "--status", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "healthy" in result.output
        assert "Claude Code" in result.output
        mock_client.get_agent_health.assert_called_once_with(agent_name="Claude Code")

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_agent_health_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(cli, ["agent", "health", "--ok"])
        assert result.exit_code != 0

    def test_agent_health_no_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["agent", "health"])
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_agent_health_with_pending_messages(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.submit_agent_health.return_value = {
            "agent_name": "Claude Code",
            "status": "healthy",
            "last_check": "2025-01-01T00:00:00Z",
            "history": [],
            "pending_messages": [
                {
                    "id": "uuid-1",
                    "content": "Please review PR #42",
                    "message_type": "text",
                    "sender_type": "human",
                    "sender_name": "John Doe",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                {
                    "id": "uuid-2",
                    "content": "New deployment ready",
                    "message_type": "system",
                    "sender_type": "system",
                    "sender_name": None,
                    "created_at": "2025-01-01T00:00:00Z",
                },
            ],
        }

        result = runner.invoke(
            cli, ["agent", "health", "--ok", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "Pending messages (2)" in result.output
        assert "Please review PR #42" in result.output
        assert "John Doe" in result.output
        assert "New deployment ready" in result.output
        assert "[system]:" in result.output

    # --- Webhook tests ---

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_webhook_register(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.register_agent_webhook.return_value = {
            "agent_name": "Claude Code",
            "webhook_url": "https://my-server.com/hook",
        }

        result = runner.invoke(
            cli,
            ["agent", "webhook", "register", "--url", "https://my-server.com/hook",
             "--secret", "my-token", "--name", "Claude Code"],
        )
        assert result.exit_code == 0
        assert "Webhook Registered" in result.output
        assert "https://my-server.com/hook" in result.output
        mock_client.register_agent_webhook.assert_called_once_with(
            agent_name="Claude Code",
            webhook_url="https://my-server.com/hook",
            webhook_secret="my-token",
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_webhook_unregister(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.unregister_agent_webhook.return_value = {
            "detail": "Webhook unregistered.",
        }

        result = runner.invoke(
            cli, ["agent", "webhook", "unregister", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "Webhook unregistered" in result.output

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_webhook_register_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(
            cli, ["agent", "webhook", "register", "--url", "https://example.com/hook"]
        )
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_webhook_unregister_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(cli, ["agent", "webhook", "unregister"])
        assert result.exit_code != 0

    # --- Message tests ---

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_message_send(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.send_agent_message.return_value = {
            "id": "msg-uuid",
            "agent_name": "Claude Code",
            "content": "Review PR #42",
            "message_type": "text",
            "sender_type": "agent",
            "sender_name": "CLI Agent",
            "delivered": False,
            "created_at": "2025-01-01T00:00:00Z",
        }

        result = runner.invoke(
            cli,
            ["agent", "message", "send", "--to", "Claude Code", "--content", "Review PR #42"],
        )
        assert result.exit_code == 0
        assert "Message Sent" in result.output
        assert "Review PR #42" in result.output
        assert "CLI Agent" in result.output
        mock_client.send_agent_message.assert_called_once_with(
            agent_name="Claude Code",
            content="Review PR #42",
            message_type=None,
            metadata=None,
            expires_at=None,
            sender_type="agent",
            sender_name="CLI Agent",
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_message_send_with_type(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.send_agent_message.return_value = {
            "id": "msg-uuid",
            "agent_name": "Claude Code",
            "content": "Do X",
            "message_type": "command",
            "sender_type": "agent",
            "sender_name": "My Bot",
            "delivered": False,
            "created_at": "2025-01-01T00:00:00Z",
        }

        result = runner.invoke(
            cli,
            ["agent", "message", "send", "--to", "Claude Code",
             "--content", "Do X", "--type", "command", "--name", "My Bot"],
        )
        assert result.exit_code == 0
        assert "Message Sent" in result.output
        mock_client.send_agent_message.assert_called_once_with(
            agent_name="Claude Code",
            content="Do X",
            message_type="command",
            metadata=None,
            expires_at=None,
            sender_type="agent",
            sender_name="My Bot",
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_message_list(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.get_agent_messages.return_value = [
            {
                "id": "msg-1",
                "content": "Review PR #42",
                "message_type": "text",
                "sender_type": "human",
                "sender_name": "John Doe",
                "delivered": False,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "id": "msg-2",
                "content": "Deploy done",
                "message_type": "system",
                "sender_type": "agent",
                "sender_name": "CI Bot",
                "delivered": True,
                "created_at": "2025-01-01T01:00:00Z",
            },
        ]

        result = runner.invoke(
            cli, ["agent", "message", "list", "--name", "Claude Code"]
        )
        assert result.exit_code == 0
        assert "Review PR #42" in result.output
        assert "John Doe" in result.output
        assert "Deploy done" in result.output
        assert "CI Bot" in result.output
        mock_client.get_agent_messages.assert_called_once_with(
            agent_name="Claude Code", delivered=None
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    @patch("dailybot_cli.commands.agent.DailyBotClient")
    def test_message_list_pending(
        self, mock_client_cls: MagicMock, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = "api_key"
        mock_client: MagicMock = mock_client_cls.return_value
        mock_client.get_agent_messages.return_value = []

        result = runner.invoke(
            cli, ["agent", "message", "list", "--name", "Claude Code", "--pending"]
        )
        assert result.exit_code == 0
        assert "No messages" in result.output
        mock_client.get_agent_messages.assert_called_once_with(
            agent_name="Claude Code", delivered=False
        )

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_message_send_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(
            cli, ["agent", "message", "send", "--to", "Bot", "--content", "hi"]
        )
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_message_list_no_api_key(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(cli, ["agent", "message", "list", "--name", "Bot"])
        assert result.exit_code != 0

    @patch("dailybot_cli.commands.agent.get_agent_auth")
    def test_agent_no_auth(
        self, mock_get_auth: MagicMock, runner: CliRunner
    ) -> None:
        mock_get_auth.return_value = None
        result = runner.invoke(cli, ["agent", "update", "test"])
        assert result.exit_code != 0
        assert "dailybot config key=" in result.output
        assert "dailybot login" in result.output


class TestConfigCommand:

    @pytest.fixture(autouse=True)
    def _tmp_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_dir: Path = tmp_path / ".config" / "dailybot"
        monkeypatch.setattr("dailybot_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("dailybot_cli.config.CONFIG_FILE", config_dir / "config.json")
        monkeypatch.setattr("dailybot_cli.config.CREDENTIALS_FILE", config_dir / "credentials.json")

    def test_config_set_key(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["config", "key=abc123"])
        assert result.exit_code == 0
        assert "API key saved" in result.output
        assert "abc1****" in result.output

    def test_config_show_key(self, runner: CliRunner) -> None:
        runner.invoke(cli, ["config", "key=secretkey99"])
        result = runner.invoke(cli, ["config", "key"])
        assert result.exit_code == 0
        assert "secr****" in result.output

    def test_config_show_key_not_set(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["config", "key"])
        assert result.exit_code == 0
        assert "not set" in result.output

    def test_config_unset_key(self, runner: CliRunner) -> None:
        runner.invoke(cli, ["config", "key=abc123"])
        result = runner.invoke(cli, ["config", "key="])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_config_unknown_setting(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["config", "foo=bar"])
        assert result.exit_code != 0
        assert "Unknown setting" in result.output
