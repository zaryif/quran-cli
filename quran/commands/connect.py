"""
quran connect — manage all notification channels.

Usage:
  quran connect list
  quran connect telegram
  quran connect whatsapp
  quran connect gmail
  quran connect webhook https://...
  quran connect test telegram
  quran connect off telegram
  quran connect on  telegram
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Notification channel management.")
console = Console()


@app.callback(invoke_without_command=True)
def connect_cmd(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        list_connectors()


@app.command("list")
def list_connectors():
    """Show all notification channels and their status."""
    from quran.connectors import ALL_CONNECTORS, load_connectors

    cfg = load_connectors()

    table = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="dim",
                  border_style="bright_black", padding=(0, 2))
    table.add_column("Channel",   width=12)
    table.add_column("Status",    width=16)
    table.add_column("Notes",     width=40, style="dim")

    notes = {
        "desktop":  "OS-native popups — always available",
        "ntfy":     "Free phone push — install ntfy app",
        "telegram": "Telegram bot — setup via BotFather",
        "whatsapp": "WhatsApp via Twilio (~$0.005/msg)",
        "gmail":    "Gmail digest / per-prayer emails",
        "webhook":  "Discord, Slack, Home Assistant, etc.",
    }

    for name, connector in ALL_CONNECTORS.items():
        ccfg = cfg.get(name, {})
        enabled = ccfg.get("enabled", name == "desktop")
        configured = connector.is_configured(ccfg) or name == "desktop"

        if enabled and configured:
            status = "[bold green]● active[/bold green]"
        elif enabled and not configured:
            status = "[yellow]○ not set up[/yellow]"
        else:
            status = "[dim]○ disabled[/dim]"

        table.add_row(name, status, notes.get(name, ""))

    console.print()
    console.print(table)
    console.print()
    console.print("  [dim]Setup: [green]quran connect <channel>[/green]")
    console.print("  [dim]Test:  [green]quran connect test <channel>[/green][/dim]\n")


@app.command("telegram")
def setup_telegram():
    """Set up Telegram bot notifications."""
    from quran.connectors import TelegramConnector, load_connectors, save_connectors
    c = TelegramConnector()
    result = c.setup()
    data = load_connectors()
    data["telegram"] = result
    save_connectors(data)
    console.print(f"\n[green]✓[/green] Telegram saved. Run [green]quran connect test telegram[/green] to verify.\n")


@app.command("whatsapp")
def setup_whatsapp():
    """Set up WhatsApp (Twilio) notifications."""
    from quran.connectors import WhatsAppConnector, load_connectors, save_connectors
    c = WhatsAppConnector()
    result = c.setup()
    data = load_connectors()
    data["whatsapp"] = result
    save_connectors(data)
    console.print(f"\n[green]✓[/green] WhatsApp saved. Run [green]quran connect test whatsapp[/green] to verify.\n")


@app.command("gmail")
def setup_gmail():
    """Set up Gmail reminder emails."""
    from quran.connectors import GmailConnector, load_connectors, save_connectors
    c = GmailConnector()
    result = c.setup()
    data = load_connectors()
    data["gmail"] = result
    save_connectors(data)
    console.print(f"\n[green]✓[/green] Gmail saved. Run [green]quran connect test gmail[/green] to verify.\n")


@app.command("ntfy")
def setup_ntfy():
    """Set up ntfy.sh phone push notifications."""
    from quran.connectors import load_connectors, save_connectors
    import secrets

    data  = load_connectors()
    topic = data.get("ntfy", {}).get("topic") or f"quran-{secrets.token_hex(6)}"
    data["ntfy"] = {"enabled": True, "topic": topic}
    save_connectors(data)

    url = f"https://ntfy.sh/{topic}"
    console.print()
    console.print(Rule("[dim]ntfy.sh Phone Push[/dim]", style="green"))
    console.print()
    console.print(f"  1. Install [bold]ntfy[/bold] app on iOS/Android: [green]ntfy.sh[/green]")
    console.print(f"  2. Subscribe to: [bold green]{url}[/bold green]")
    console.print()

    try:
        import qrcode
        from io import StringIO
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        f = StringIO()
        qr.print_ascii(out=f, invert=True)
        console.print(f.getvalue())
    except ImportError:
        pass

    console.print(f"  [green]✓[/green] ntfy configured with topic: [dim]{topic}[/dim]\n")


@app.command("webhook")
def setup_webhook(
    url: Annotated[str, typer.Argument(help="Webhook URL (Discord/Slack/custom)")],
):
    """Set a custom webhook URL for notifications."""
    from quran.connectors import load_connectors, save_connectors
    data = load_connectors()
    data["webhook"] = {"enabled": True, "url": url}
    save_connectors(data)
    console.print(f"\n[green]✓[/green] Webhook set: [dim]{url}[/dim]")
    console.print(f"  Run [green]quran connect test webhook[/green] to verify.\n")


@app.command("test")
def test_connector(
    channel: Annotated[str, typer.Argument(help="Channel to test: telegram/whatsapp/gmail/ntfy/webhook/desktop")],
):
    """Send a test notification to a channel."""
    from quran.connectors import ALL_CONNECTORS, load_connectors

    c = ALL_CONNECTORS.get(channel.lower())
    if not c:
        console.print(f"[red]✗[/red] Unknown channel: {channel}")
        return

    with console.status(f"[dim]Sending test to {channel}…[/dim]"):
        ok = c.test()

    if ok:
        console.print(f"[green]✓[/green] Test sent to [bold]{channel}[/bold].")
    else:
        console.print(f"[red]✗[/red] Failed. Run [green]quran connect {channel}[/green] to reconfigure.")


@app.command("off")
def disable_connector(
    channel: Annotated[str, typer.Argument()],
):
    """Disable a notification channel."""
    from quran.connectors import load_connectors, save_connectors
    data = load_connectors()
    if channel in data:
        data[channel]["enabled"] = False
        save_connectors(data)
        console.print(f"[green]✓[/green] {channel} disabled.")
    else:
        console.print(f"[dim]{channel} was not configured.[/dim]")


@app.command("on")
def enable_connector(
    channel: Annotated[str, typer.Argument()],
):
    """Re-enable a notification channel."""
    from quran.connectors import load_connectors, save_connectors
    data = load_connectors()
    if channel in data:
        data[channel]["enabled"] = True
        save_connectors(data)
        console.print(f"[green]✓[/green] {channel} enabled.")
    else:
        console.print(f"[red]✗[/red] {channel} not configured yet. Run [green]quran connect {channel}[/green]")
