"""DailyBot CLI entry point."""

import click

from dailybot_cli import __version__
from dailybot_cli.commands.agent import agent
from dailybot_cli.commands.auth import auth
from dailybot_cli.commands.interactive import run_interactive
from dailybot_cli.commands.status import status
from dailybot_cli.commands.update import update


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="dailybot")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """DailyBot CLI - Submit check-in updates from your terminal.

    \b
    Quick start:
      dailybot auth login          # Authenticate with email OTP
      dailybot status              # View pending check-ins
      dailybot update "message"    # Submit a free-text update
      dailybot update --done "X" --doing "Y" --blocked "None"

    \b
    Agent mode (requires DAILYBOT_API_KEY env var):
      dailybot agent update "Deployed v2.1" --name "My Agent"

    Run without arguments for interactive mode.
    """
    if ctx.invoked_subcommand is None:
        run_interactive()


cli.add_command(auth)
cli.add_command(update)
cli.add_command(status)
cli.add_command(agent)


if __name__ == "__main__":
    cli()
