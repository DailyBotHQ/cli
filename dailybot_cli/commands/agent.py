"""Agent commands for DailyBot CLI (API key authentication)."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_api_key
from dailybot_cli.display import console, print_error, print_success


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
