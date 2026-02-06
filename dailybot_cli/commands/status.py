"""Status command for DailyBot CLI."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_token
from dailybot_cli.display import console, print_error, print_pending_checkins


@click.command()
def status() -> None:
    """Show pending check-ins for today."""
    token: Optional[str] = get_token()
    if not token:
        print_error("Not logged in. Run: dailybot login")
        raise SystemExit(1)

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Fetching pending check-ins..."):
            data: dict[str, Any] = client.get_status()
        checkins: list[dict[str, Any]] = data.get("pending_checkins", [])
        print_pending_checkins(checkins)
    except APIError as e:
        if e.status_code in (401, 403):
            print_error("Session expired. Please log in again: dailybot login")
        else:
            print_error(e.detail)
        raise SystemExit(1)
