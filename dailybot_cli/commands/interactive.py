"""Interactive mode for DailyBot CLI."""

from typing import Any, Optional

import click
import questionary

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_token, load_credentials, save_credentials
from dailybot_cli.display import (
    console,
    print_error,
    print_info,
    print_org_selection,
    print_pending_checkins,
    print_success,
    print_update_result,
)


MENU_SEND_UPDATE: str = "Send update"
MENU_VIEW_PENDING: str = "View pending check-ins"
MENU_AUTH_STATUS: str = "Auth status"
MENU_QUIT: str = "Quit"

MENU_CHOICES: list[str] = [
    MENU_SEND_UPDATE,
    MENU_VIEW_PENDING,
    MENU_AUTH_STATUS,
    MENU_QUIT,
]


def _interactive_login() -> None:
    """Guide the user through authentication inside interactive mode."""
    console.print()
    print_info("Let's get you logged in.")
    console.print()

    email: str = click.prompt("Email")
    client: DailyBotClient = DailyBotClient()

    try:
        with console.status("Sending verification code..."):
            client.request_code(email)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)

    print_success(f"Verification code sent to {email}")
    print_info("Check your inbox (including spam folder).")

    code: str = click.prompt("Enter the 6-digit code", type=str).strip()

    try:
        with console.status("Verifying code..."):
            result: dict[str, Any] = client.verify_code(email, code)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)

    if result.get("organization_selection_required"):
        organizations: list[dict[str, Any]] = result.get("organizations", [])
        print_info("You belong to multiple organizations. Please select one:")
        print_org_selection(organizations)
        choice: int = click.prompt("Select organization number", type=int)
        if choice < 1 or choice > len(organizations):
            print_error("Invalid selection.")
            raise SystemExit(1)
        selected_org: dict[str, Any] = organizations[choice - 1]
        try:
            with console.status("Verifying..."):
                result = client.verify_code(email, code, organization_id=selected_org["id"])
        except APIError as e:
            print_error(e.detail)
            raise SystemExit(1)

    token: Optional[str] = result.get("token")
    if not token:
        print_error("Authentication failed: no token received.")
        raise SystemExit(1)

    org_raw: Any = result.get("organization", "")
    org_name: str = org_raw.get("name", "") if isinstance(org_raw, dict) else str(org_raw)
    org_uuid: str = org_raw.get("uuid", "") if isinstance(org_raw, dict) else result.get("organization_uuid", "")
    save_credentials(
        token=token,
        email=email,
        organization=org_name,
        organization_uuid=org_uuid,
        api_url=client.api_url,
    )
    print_success(f"Logged in as {email} ({org_name})")


def run_interactive() -> None:
    """Run the interactive TUI mode."""
    creds: Optional[dict[str, Any]] = load_credentials()
    token: Optional[str] = get_token()

    console.print(f"\n[bold]DailyBot CLI[/bold]")

    if not token or not creds:
        _interactive_login()
        creds = load_credentials()

    email: str = creds.get("email", "") if creds else ""
    org_stored: Any = creds.get("organization", "") if creds else ""
    org: str = org_stored.get("name", "") if isinstance(org_stored, dict) else str(org_stored)
    console.print(f"Logged in as {email} ({org})\n")

    client: DailyBotClient = DailyBotClient()

    while True:
        console.print()
        choice: Optional[str] = questionary.select(
            "What would you like to do?",
            choices=MENU_CHOICES,
        ).ask()

        if choice is None or choice == MENU_QUIT:
            print_info("Goodbye!")
            break
        elif choice == MENU_SEND_UPDATE:
            _send_update(client)
        elif choice == MENU_VIEW_PENDING:
            _view_pending(client)
        elif choice == MENU_AUTH_STATUS:
            _show_auth(client)


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
