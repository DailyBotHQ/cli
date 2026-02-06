"""Update command for DailyBot CLI."""

from typing import Any, Optional

import click

from dailybot_cli.api_client import APIError, DailyBotClient
from dailybot_cli.config import get_token
from dailybot_cli.display import console, print_error, print_info, print_update_result


def _require_auth() -> DailyBotClient:
    """Ensure user is authenticated, return a client."""
    token: Optional[str] = get_token()
    if not token:
        print_error("Not logged in. Run: dailybot auth login")
        raise SystemExit(1)
    return DailyBotClient()


@click.command()
@click.argument("message", required=False)
@click.option("--done", "-d", help="What you completed.")
@click.option("--doing", "-w", help="What you are working on.")
@click.option("--blocked", "-b", help="Any blockers.")
def update(
    message: Optional[str],
    done: Optional[str],
    doing: Optional[str],
    blocked: Optional[str],
) -> None:
    """Submit a check-in update.

    You can provide a free-text message or use structured flags:

    \b
      dailybot update "I finished the auth module and now working on tests."
      dailybot update --done "Auth module" --doing "Tests" --blocked "None"
    """
    client: DailyBotClient = _require_auth()

    # If no args at all, prompt for input
    if not message and not done and not doing and not blocked:
        print_info("Enter your update (press Enter twice to submit):")
        lines: list[str] = []
        empty_count: int = 0
        while True:
            try:
                line: str = input()
            except EOFError:
                break
            if line == "":
                empty_count += 1
                if empty_count >= 1 and lines:
                    break
                lines.append("")
            else:
                empty_count = 0
                lines.append(line)
        message = "\n".join(lines).strip()
        if not message:
            print_error("Empty update. Nothing sent.")
            raise SystemExit(1)

    try:
        with console.status("Submitting update..."):
            result: dict[str, Any] = client.submit_update(
                message=message,
                done=done,
                doing=doing,
                blocked=blocked,
            )
        print_update_result(result)
    except APIError as e:
        if e.status_code in (401, 403):
            print_error("Session expired. Please log in again: dailybot auth login")
        else:
            print_error(e.detail)
        raise SystemExit(1)
