"""
quran bot — run the Telegram prayer reminder bot.

The bot sends prayer reminders, ayah of the day, Ramadan timings,
and responds to Quran/Hadith queries on Telegram — all free via
the official Telegram Bot API.

Usage:
  quran bot start       # start the bot (blocking)
  quran bot status      # check if configured
  quran bot setup       # interactive setup wizard
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.rule import Rule
from rich.panel import Panel
from typing_extensions import Annotated

app     = typer.Typer(help="Run the Telegram prayer reminder bot.")
console = Console()


@app.callback(invoke_without_command=True)
def bot_cmd(ctx: typer.Context):
    """Manage the Telegram prayer reminder bot."""
    if ctx.invoked_subcommand:
        return
    _show_status()


@app.command("start")
def bot_start(
    token: Annotated[str, typer.Option(
        "--token", "-t", help="Bot token (or set TELEGRAM_BOT_TOKEN env var)"
    )] = "",
):
    """Start the Telegram bot (runs in foreground)."""
    from quran.bot.telegram_bot import run

    console.print()
    console.print(Rule("[dim]quran-cli Telegram Bot[/dim]", style="green"))
    console.print()
    console.print("  [dim]Starting Telegram bot…[/dim]")
    console.print("  [dim]Press Ctrl+C to stop.[/dim]\n")

    run(token=token or None)


@app.command("setup")
def bot_setup():
    """Interactive setup wizard for the Telegram bot."""
    console.print()
    console.print(Rule("[dim]Telegram Bot Setup[/dim]", style="green"))
    console.print()
    console.print("  [bold]Step 1[/bold] — Create a bot on Telegram:")
    console.print("  [dim]1. Open Telegram and search [green]@BotFather[/green][/dim]")
    console.print("  [dim]2. Send [green]/newbot[/green][/dim]")
    console.print("  [dim]3. Follow the instructions to get your [bold]Bot Token[/bold][/dim]")
    console.print()
    console.print("  [dim]Then run: [green]quran connect telegram[/green][/dim]")
    console.print("  [dim]Then run: [green]quran bot start[/green][/dim]")
    console.print()
    console.print("  [bold]Step 2[/bold] — Subscribe:")
    console.print("  [dim]Open your new bot on Telegram and send [green]/start[/green][/dim]")
    console.print()
    console.print(
        Panel(
            "[dim]The bot will send:\n"
            "  · Prayer time notifications (5 daily)\n"
            "  · Sehri warning 15 min before Fajr (Ramadan)\n"
            "  · Iftar alert at Maghrib (Ramadan)\n"
            "  · Daily ayah at 7 AM\n"
            "  · Laylatul Qadr alerts (last 10 nights)\n\n"
            "Bot commands after /start:\n"
            "  /pray · /schedule · /ramadan · /ayah · /hadith\n"
            "  /setlocation <city> · /setmethod <method> · /stop[/dim]",
            title="[dim]what the bot does[/dim]",
            border_style="bright_black",
            padding=(1, 2),
        )
    )
    console.print()


@app.command("status")
def bot_status():
    """Check if the Telegram bot is configured."""
    from quran.connectors.connectors import load_connectors

    cfg   = load_connectors()
    tg    = cfg.get("telegram", {})
    token = tg.get("token", "")
    cid   = tg.get("chat_id", "")

    console.print()
    if token and cid:
        console.print(f"  [green]✓[/green] Token:    [dim]...{token[-8:]}[/dim]")
        console.print(f"  [green]✓[/green] Chat ID:  [dim]{cid}[/dim]")
        console.print(f"\n  [dim]Run [green]quran bot start[/green] to launch the bot.[/dim]\n")
    elif token:
        console.print(f"  [green]✓[/green] Token configured")
        console.print(f"  [yellow]○[/yellow] Chat ID missing — send [green]/start[/green] to the bot on Telegram.\n")
    else:
        console.print("  [dim]Telegram bot not configured.[/dim]")
        console.print("  [dim]Run [green]quran bot setup[/green] to get started.[/dim]\n")
