"""Agent commands for DailyBot CLI (API key authentication)."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_api_key
from dailybot_cli.display import (
    console,
    print_agent_health,
    print_agent_message_sent,
    print_agent_messages,
    print_error,
    print_success,
    print_webhook_result,
)


@click.group()
def agent() -> None:
    """Agent commands (requires DAILYBOT_API_KEY)."""
    pass


@agent.command(name="update")
@click.argument("content")
@click.option("--name", "-n", default="CLI Agent", help="Agent worker name.")
@click.option("--json-data", "-j", help="Structured JSON data to include.")
def agent_update(content: str, name: str, json_data: Optional[str]) -> None:
    """Submit an agent activity report.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent update "Deployed v2.1 to staging"
      DAILYBOT_API_KEY=xxx dailybot agent update "Built feature X" --name "Claude Code"
    """
    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    structured: Optional[dict[str, Any]] = None
    if json_data:
        import json

        try:
            structured = json.loads(json_data)
        except json.JSONDecodeError:
            print_error("Invalid JSON in --json-data.")
            raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Submitting agent report..."):
            result: dict[str, Any] = client.submit_agent_report(
                agent_name=name,
                content=content,
                structured=structured,
            )
        print_success(f"Report submitted (id: {result.get('id', 'N/A')})")
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)


@agent.command(name="health")
@click.option("--ok", "report_ok", is_flag=True, default=False, help="Report healthy status.")
@click.option("--fail", "report_fail", is_flag=True, default=False, help="Report unhealthy status.")
@click.option("--status", "query_status", is_flag=True, default=False, help="Query current health status.")
@click.option("--message", "-m", default=None, help="Optional message to include.")
@click.option("--name", "-n", default="CLI Agent", help="Agent worker name.")
def agent_health(
    report_ok: bool,
    report_fail: bool,
    query_status: bool,
    message: Optional[str],
    name: str,
) -> None:
    """Report or query agent health status.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent health --ok --message "All good"
      DAILYBOT_API_KEY=xxx dailybot agent health --fail --message "DB unreachable"
      DAILYBOT_API_KEY=xxx dailybot agent health --status --name "Claude Code"
    """
    flags: int = sum([report_ok, report_fail, query_status])
    if flags != 1:
        print_error("Specify exactly one of --ok, --fail, or --status.")
        raise SystemExit(1)

    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        if query_status:
            with console.status("Fetching agent health..."):
                result: dict[str, Any] = client.get_agent_health(agent_name=name)
            print_agent_health(result)
        else:
            with console.status("Submitting agent health..."):
                result = client.submit_agent_health(
                    agent_name=name,
                    ok=report_ok,
                    message=message,
                )
            print_agent_health(result)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)


# --- Webhook subcommand group ---


@agent.group(name="webhook")
def agent_webhook() -> None:
    """Manage agent webhooks."""
    pass


@agent_webhook.command(name="register")
@click.option("--url", required=True, help="Webhook URL to receive POST requests.")
@click.option("--secret", default=None, help="Secret sent as X-Webhook-Secret header.")
@click.option("--name", "-n", default="CLI Agent", help="Agent worker name.")
def webhook_register(url: str, secret: Optional[str], name: str) -> None:
    """Register a webhook for the agent.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent webhook register --url https://my-server.com/hook
      DAILYBOT_API_KEY=xxx dailybot agent webhook register --url https://... --secret my-token
    """
    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Registering webhook..."):
            result: dict[str, Any] = client.register_agent_webhook(
                agent_name=name,
                webhook_url=url,
                webhook_secret=secret,
            )
        print_webhook_result(result)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)


@agent_webhook.command(name="unregister")
@click.option("--name", "-n", default="CLI Agent", help="Agent worker name.")
def webhook_unregister(name: str) -> None:
    """Unregister the agent's webhook.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent webhook unregister
      DAILYBOT_API_KEY=xxx dailybot agent webhook unregister --name "Claude Code"
    """
    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Unregistering webhook..."):
            result: dict[str, Any] = client.unregister_agent_webhook(agent_name=name)
        print_success(result.get("detail", "Webhook unregistered."))
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)


# --- Message subcommand group ---


@agent.group(name="message")
def agent_message() -> None:
    """Send and list agent messages."""
    pass


@agent_message.command(name="send")
@click.option("--to", "to_agent", required=True, help="Target agent name.")
@click.option("--content", required=True, help="Message content.")
@click.option("--type", "message_type", default=None, help="Message type: text, command, or system.")
@click.option("--name", "-n", default="CLI Agent", help="Sender agent name.")
@click.option("--json-data", "-j", default=None, help="JSON metadata to include.")
@click.option("--expires-at", default=None, help="ISO 8601 expiration timestamp.")
def message_send(
    to_agent: str,
    content: str,
    message_type: Optional[str],
    name: str,
    json_data: Optional[str],
    expires_at: Optional[str],
) -> None:
    """Send a message to an agent.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent message send --to "Claude Code" --content "Review PR #42"
      DAILYBOT_API_KEY=xxx dailybot agent message send --to "Claude Code" --content "Do X" --type command
    """
    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    metadata: Optional[dict[str, Any]] = None
    if json_data:
        import json

        try:
            metadata = json.loads(json_data)
        except json.JSONDecodeError:
            print_error("Invalid JSON in --json-data.")
            raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Sending message..."):
            result: dict[str, Any] = client.send_agent_message(
                agent_name=to_agent,
                content=content,
                message_type=message_type,
                metadata=metadata,
                expires_at=expires_at,
                sender_type="agent",
                sender_name=name,
            )
        print_agent_message_sent(result)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)


@agent_message.command(name="list")
@click.option("--name", "-n", required=True, help="Agent name to list messages for.")
@click.option("--pending", is_flag=True, default=False, help="Show only undelivered messages.")
def message_list(name: str, pending: bool) -> None:
    """List messages for an agent.

    \b
      DAILYBOT_API_KEY=xxx dailybot agent message list --name "Claude Code"
      DAILYBOT_API_KEY=xxx dailybot agent message list --name "Claude Code" --pending
    """
    api_key: Optional[str] = get_api_key()
    if not api_key:
        print_error("DAILYBOT_API_KEY environment variable is required for agent commands.")
        raise SystemExit(1)

    delivered: Optional[bool] = False if pending else None
    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Fetching messages..."):
            messages: list[dict[str, Any]] = client.get_agent_messages(
                agent_name=name,
                delivered=delivered,
            )
        print_agent_messages(messages)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)
