"""
quran config — view and update all settings.

Usage:
  quran config show
  quran config set lang bn
  quran config set lang2 ur
  quran config set method Karachi
  quran config set location auto
  quran config set display.arabic true
  quran config set display.show_en true
  quran config set display.show_lang2 true
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
    from quran.commands.lang import LANGUAGES

    cfg = load()
    console.print()
    console.print(Rule(f"[dim]{CONFIG_FILE}[/dim]", style="bright_black"))
    console.print()

    lang  = cfg.get("lang", "en")
    lang2 = cfg.get("lang2", "bn")
    console.print(f"  [dim]Primary language:[/dim]   [bold green]{lang}[/bold green]  {LANGUAGES.get(lang, {}).get('native', '')}")
    console.print(f"  [dim]Secondary language:[/dim] [bold cyan]{lang2}[/bold cyan]  {LANGUAGES.get(lang2, {}).get('native', '')}")
    console.print()

    table = Table(box=box.SIMPLE, show_header=False,
                  border_style="bright_black", padding=(0,2))
    table.add_column("Key",   style="dim",   width=30)
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
    console.print(f"  [dim]Change language: [green]quran lang[/green][/dim]")
    console.print(f"  [dim]Edit any setting: [green]quran config set <key> <value>[/green][/dim]\n")


@app.command("set")
def set_config(
    key:   Annotated[str, typer.Argument(
        help="Key (dot notation): lang, lang2, method, asr_method, location.city, display.arabic, display.show_en, display.show_lang2 …")],
    value: Annotated[str, typer.Argument(help="New value")],
):
    """Set any config value using dot notation."""
    from quran.config.settings import set_key, load, save
    from quran.core.prayer_times import METHODS
    from quran.commands.lang import LANGUAGES

    # ── Special cases ──────────────────────────────────────────────────────────

    # location auto
    if key == "location" and value == "auto":
        from quran.core.location import detect_location
        with console.status("[dim]Detecting location…[/dim]"):
            loc = detect_location(force=True)
        cfg = load()
        cfg["location"] = loc
        save(cfg)
        console.print(f"[green]✓[/green] Location: [bold]{loc['city']}, {loc['country']}[/bold]")
        return

    # lang — validate and show preview
    if key == "lang":
        if value not in LANGUAGES:
            console.print(f"[red]✗[/red] Unknown language '{value}'.")
            console.print(f"  Options: {', '.join(LANGUAGES.keys())}")
            console.print(f"  Run [green]quran lang --list[/green] for full table.")
            return
        set_key("lang", value)
        lang2 = load().get("lang2", "bn")
        name  = LANGUAGES[value]["name"]
        console.print(f"[green]✓[/green] Primary language → [bold green]{name} ({value})[/bold green]")
        console.print(f"  [dim]Run [green]quran[/green] to see updated splash screen.[/dim]")
        return

    # lang2 — secondary splash language
    if key == "lang2":
        if value not in LANGUAGES:
            console.print(f"[red]✗[/red] Unknown language '{value}'.")
            console.print(f"  Options: {', '.join(LANGUAGES.keys())}")
            return
        set_key("lang2", value)
        name = LANGUAGES[value]["name"]
        console.print(f"[green]✓[/green] Secondary language → [bold cyan]{name} ({value})[/bold cyan]")
        console.print(f"  [dim]Run [green]quran[/green] to see updated splash screen.[/dim]")
        return

    # method — validate
    if key == "method" and value not in METHODS:
        console.print(f"[red]✗[/red] Unknown method '{value}'. Options: {', '.join(METHODS.keys())}")
        return

    # boolean coercion for display settings
    if key.startswith("display."):
        if value.lower() in ("true", "yes", "on", "1"):
            value = "true"
        elif value.lower() in ("false", "no", "off", "0"):
            value = "false"

    # Generic set
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
