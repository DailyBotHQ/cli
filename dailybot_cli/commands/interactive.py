"""Interactive mode for DailyBot CLI."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_token, load_credentials
from dailybot_cli.display import (
    console,
    print_error,
    print_info,
    print_pending_checkins,
    print_success,
    print_update_result,
)


MENU_OPTIONS: list[tuple[str, str]] = [
    ("1", "Send update"),
    ("2", "View pending check-ins"),
    ("3", "Auth status"),
    ("q", "Quit"),
]


def run_interactive() -> None:
    """Run the interactive TUI mode."""
    creds: Optional[dict[str, Any]] = load_credentials()
    token: Optional[str] = get_token()

    if not token or not creds:
        print_info("Not logged in. Run: dailybot auth login")
        raise SystemExit(1)

    email: str = creds.get("email", "")
    org: str = creds.get("organization", "")
    console.print(f"[bold]DailyBot CLI[/bold] - {email} ({org})\n")

    client: DailyBotClient = DailyBotClient()

    while True:
        console.print()
        for key, label in MENU_OPTIONS:
            console.print(f"  [bold]{key}[/bold]) {label}")
        console.print()

        choice: str = click.prompt("Choose", type=str, default="1").strip().lower()

        if choice == "1":
            _send_update(client)
        elif choice == "2":
            _view_pending(client)
        elif choice == "3":
            _show_auth(client)
        elif choice in ("q", "quit", "exit"):
            print_info("Goodbye!")
            break
        else:
            print_error("Invalid choice.")


def _send_update(client: DailyBotClient) -> None:
    """Prompt for and send an update."""
    print_info("Enter your update (press Enter on empty line to submit):")
    lines: list[str] = []
    while True:
        try:
            line: str = input("> ")
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)

    message: str = "\n".join(lines).strip()
    if not message:
        print_error("Empty update. Nothing sent.")
        return

    try:
        with console.status("Submitting update..."):
            result: dict[str, Any] = client.submit_update(message=message)
        print_update_result(result)
    except APIError as e:
        print_error(e.detail)


def _view_pending(client: DailyBotClient) -> None:
    """Fetch and display pending check-ins."""
    try:
        with console.status("Fetching..."):
            data: dict[str, Any] = client.get_status()
        checkins: list[dict[str, Any]] = data.get("pending_checkins", [])
        print_pending_checkins(checkins)
    except APIError as e:
        print_error(e.detail)


def _show_auth(client: DailyBotClient) -> None:
    """Show current auth status."""
    try:
        data: dict[str, Any] = client.auth_status()
        print_success(f"Logged in as {data.get('email', '')} ({data.get('organization', '')})")
    except APIError as e:
        print_error(e.detail)
