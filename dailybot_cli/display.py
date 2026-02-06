"""Rich console output helpers for DailyBot CLI."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console: Console = Console()
error_console: Console = Console(stderr=True)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]OK[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    error_console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[dim]{message}[/dim]")


def print_auth_status(data: dict[str, Any]) -> None:
    """Display auth status information."""
    table: Table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Email", str(data.get("email", "")))
    table.add_row("Organization", str(data.get("organization", "")))
    table.add_row("Expires", str(data.get("expires_at", "")))
    console.print(Panel(table, title="[bold]Auth Status[/bold]", border_style="green"))


def print_pending_checkins(checkins: list[dict[str, Any]]) -> None:
    """Display pending check-ins."""
    if not checkins:
        print_info("No pending check-ins for today.")
        return

    for checkin in checkins:
        name: str = checkin.get("followup_name", "Check-in")
        questions: list[dict[str, Any]] = checkin.get("template_questions", [])
        content: Text = Text()
        for i, q in enumerate(questions):
            prefix: str = f"  {i + 1}. "
            content.append(prefix, style="dim")
            content.append(str(q.get("question", "")))
            if q.get("is_blocker"):
                content.append(" [blocker]", style="bold red")
            content.append("\n")
        console.print(
            Panel(
                content,
                title=f"[bold]{name}[/bold]",
                border_style="cyan",
            )
        )


def print_update_result(data: dict[str, Any]) -> None:
    """Display the result of submitting an update."""
    count: int = data.get("followups_count", 0)
    attached: list[dict[str, Any]] = data.get("attached_followups", [])
    if count == 0:
        print_warning("Update submitted but no check-ins were matched.")
        return
    print_success(f"Update submitted to {count} check-in(s)")
    for followup in attached:
        console.print(f"  [dim]-[/dim] {followup.get('followup_name', '')}")


def print_org_selection(organizations: list[dict[str, Any]]) -> None:
    """Display organization selection list."""
    table: Table = Table(show_header=True, box=None)
    table.add_column("#", style="bold")
    table.add_column("Organization")
    table.add_column("ID", style="dim")
    for i, org in enumerate(organizations, 1):
        table.add_row(str(i), str(org.get("name", "")), str(org.get("id", "")))
    console.print(table)
