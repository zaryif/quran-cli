"""
quran config — view and update all settings.

Usage:
  quran config show
  quran config set lang bn
  quran config set method Hanafi
  quran config set location auto
  quran config reset
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="View and update quran-cli settings.")
console = Console()


@app.callback(invoke_without_command=True)
def config_cmd(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        show_config()


@app.command("show")
def show_config():
    """Show current configuration."""
    from quran.config.settings import load, CONFIG_FILE

    cfg = load()
    console.print()
    console.print(Rule(f"[dim]{CONFIG_FILE}[/dim]", style="bright_black"))
    console.print()

    table = Table(box=box.SIMPLE, show_header=False,
                  border_style="bright_black", padding=(0,2))
    table.add_column("Key",   style="dim",   width=28)
    table.add_column("Value", style="white", width=30)

    def _flatten(d: dict, prefix: str = "") -> list[tuple[str,str]]:
        rows = []
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                rows.extend(_flatten(v, key))
            else:
                rows.append((key, str(v)))
        return rows

    for key, val in _flatten(cfg):
        table.add_row(key, val)

    console.print(table)
    console.print(f"  [dim]Edit: quran config set <key> <value>[/dim]\n")


@app.command("set")
def set_config(
    key:   Annotated[str, typer.Argument(help="Config key (dot notation): lang, method, location.city…")],
    value: Annotated[str, typer.Argument(help="New value")],
):
    """Set a config value."""
    from quran.config.settings import set_key, load
    from quran.core.prayer_times import METHODS

    # Special case: location auto
    if key == "location" and value == "auto":
        from quran.core.location import detect_location
        from quran.config.settings import load, save
        with console.status("[dim]Detecting location…[/dim]"):
            loc = detect_location(force=True)
        cfg = load()
        cfg["location"] = loc
        save(cfg)
        console.print(f"[green]✓[/green] Location updated: [bold]{loc['city']}, {loc['country']}[/bold]")
        return

    # Validate method
    if key == "method" and value not in METHODS:
        console.print(f"[red]✗[/red] Unknown method '{value}'. Options: {', '.join(METHODS.keys())}")
        return

    set_key(key, value)
    console.print(f"[green]✓[/green] [dim]{key}[/dim] = [bold]{value}[/bold]")


@app.command("reset")
def reset_config(
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """Reset all settings to defaults."""
    from quran.config.settings import DEFAULTS, save

    if not yes:
        console.print("[dim]Reset all settings to defaults? (y/N):[/dim] ", end="")
        if input().strip().lower() not in ("y", "yes"):
            console.print("[dim]Cancelled.[/dim]")
            return

    save(DEFAULTS)
    console.print("[green]✓[/green] Settings reset to defaults.")
