"""Authentication commands for DailyBot CLI."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import clear_credentials, get_token, save_credentials
from dailybot_cli.display import (
    console,
    print_error,
    print_info,
    print_org_selection,
    print_success,
)


def _do_login(email: str) -> None:
    """Shared login logic used by both 'dailybot login' and 'dailybot login'."""
    client: DailyBotClient = DailyBotClient()
    # Step 1: Request OTP code
    try:
        with console.status("Sending verification code..."):
            client.request_code(email)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)

    print_success(f"Verification code sent to {email}")
    print_info("Check your inbox (including spam folder).")

    # Step 2: Enter code
    code: str = click.prompt("Enter the 6-digit code", type=str)
    code = code.strip()

    # Step 3: Verify code
    try:
        with console.status("Verifying code..."):
            result: dict[str, Any] = client.verify_code(email, code)
    except APIError as e:
        print_error(e.detail)
        raise SystemExit(1)

    # Step 4: Handle multi-org
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

    # Step 5: Save credentials
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


@click.command()
@click.option("--email", prompt="Email", help="Your DailyBot account email.")
def login(email: str) -> None:
    """Authenticate with DailyBot via email OTP."""
    _do_login(email)


@click.command()
def logout() -> None:
    """Log out and revoke the current token."""
    token: Optional[str] = get_token()
    if not token:
        print_info("Not logged in.")
        return

    client: DailyBotClient = DailyBotClient()
    try:
        with console.status("Logging out..."):
            client.logout()
    except APIError:
        pass  # Revoke best-effort; clear local credentials regardless

    clear_credentials()
    print_success("Logged out.")
