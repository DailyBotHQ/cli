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
    user_raw: Any = data.get("user", "")
    email: str = user_raw.get("email", "") if isinstance(user_raw, dict) else str(user_raw or data.get("email", ""))
    org_raw: Any = data.get("organization", "")
    org_name: str = org_raw.get("name", "") if isinstance(org_raw, dict) else str(org_raw)
    org_uuid: str = org_raw.get("uuid", "") if isinstance(org_raw, dict) else ""
    table: Table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Email", email)
    table.add_row("Organization", org_name)
    if org_uuid:
        table.add_row("Org UUID", org_uuid)
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
        name: str = followup.get("followup_name", "")
        action: str = followup.get("action", "created")
        label: str = "Updated" if action == "updated" else "Submitted"
        console.print(f"  [dim]-[/dim] {name} [dim]({label})[/dim]")


