"""
quran remind — manage prayer reminders and reading goal daemon.

Usage:
  quran remind on            # start background daemon
  quran remind off           # stop daemon
  quran remind status        # check daemon status
  quran remind phone         # link phone via ntfy.sh (shows QR)
  quran remind set --goal 5ayah --at 20:00
"""
from __future__ import annotations
import secrets
import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Prayer & reading reminder daemon.")
console = Console()


@app.callback(invoke_without_command=True)
def remind_cmd(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        remind_status()


@app.command("on")
def remind_on():
    """Start the background reminder daemon."""
    from quran.config.settings import load, save
    from quran.core.scheduler import start_daemon, daemon_running

    cfg = load()
    if daemon_running():
        console.print("[green]✓[/green] Daemon is already running.")
        return

    cfg["remind"]["enabled"] = True
    save(cfg)

    console.print("[dim]Starting prayer reminder daemon…[/dim]")
    try:
        start_daemon(cfg)
        console.print("[green]✓[/green] Daemon started. You will receive prayer notifications.")
        console.print("[dim]  Stop with: [green]quran remind off[/green][/dim]")
    except Exception as e:
        console.print(f"[red]✗[/red] Could not start daemon: {e}")


@app.command("off")
def remind_off():
    """Stop the reminder daemon."""
    from quran.config.settings import load, save
    from quran.core.scheduler import stop_daemon

    cfg = load()
    cfg["remind"]["enabled"] = False
    save(cfg)

    if stop_daemon():
        console.print("[green]✓[/green] Daemon stopped.")
    else:
        console.print("[dim]Daemon was not running.[/dim]")


@app.command("status")
def remind_status():
    """Show reminder daemon status and settings."""
    from quran.config.settings import load
    from quran.core.scheduler import daemon_running

    cfg     = load()
    running = daemon_running()
    remind  = cfg.get("remind", {})

    status_s = "[bold green]● running[/bold green]" if running else "[dim]○ stopped[/dim]"
    topic    = remind.get("phone_topic", "")
    phone_s  = f"[green]linked[/green]  [dim]ntfy.sh/{topic}[/dim]" if topic else "[dim]not linked[/dim]"

    console.print(
        Panel(
            f"Daemon:    {status_s}\n"
            f"Phone:     {phone_s}\n"
            f"Goal:      [white]{remind.get('goal_ayahs', 5)} ayahs/day[/white]  "
            f"at [white]{remind.get('goal_time','20:00')}[/white]\n"
            f"Adhan:     {'[green]on[/green]' if remind.get('adhan_sound') else '[dim]off[/dim]'}",
            title="[dim]quran remind status[/dim]",
            border_style="bright_black",
            padding=(1, 2),
        )
    )


@app.command("set")
def remind_set(
    goal: Annotated[Optional[str], typer.Option("--goal", help="e.g. 5ayah or 1ruku")] = None,
    at:   Annotated[Optional[str], typer.Option("--at",   help="Time HH:MM e.g. 20:00")] = None,
    adhan:Annotated[Optional[bool],typer.Option("--adhan/--no-adhan")] = None,
):
    """Set reading goal and reminder time."""
    from quran.config.settings import load, save

    cfg = load()
    changed = []

    if goal:
        n = int("".join(filter(str.isdigit, goal)) or "5")
        cfg["remind"]["goal_ayahs"] = n
        changed.append(f"goal → [bold]{n} ayahs/day[/bold]")

    if at:
        cfg["remind"]["goal_time"] = at
        changed.append(f"time → [bold]{at}[/bold]")

    if adhan is not None:
        cfg["remind"]["adhan_sound"] = adhan
        changed.append(f"adhan → [bold]{'on' if adhan else 'off'}[/bold]")

    if changed:
        save(cfg)
        for c in changed:
            console.print(f"[green]✓[/green] {c}")
    else:
        console.print("[dim]No changes. Use --goal or --at flags.[/dim]")


@app.command("phone")
def remind_phone():
    """Link your phone for cross-device push notifications via ntfy.sh."""
    from quran.config.settings import load, save
    from quran.core.notifier import generate_phone_link

    cfg   = load()
    topic = cfg["remind"].get("phone_topic", "")

    if not topic:
        topic = f"quran-{secrets.token_hex(6)}"
        cfg["remind"]["phone_topic"] = topic
        save(cfg)

    url = generate_phone_link(topic)

    console.print()
    console.print(Rule("[dim]Phone Link — ntfy.sh[/dim]", style="green"))
    console.print()
    console.print(f"  1. Install [bold]ntfy[/bold] on your phone (iOS / Android)")
    console.print(f"     [dim]https://ntfy.sh  — free, open-source, no account needed[/dim]")
    console.print()
    console.print(f"  2. Subscribe to: [bold green]{url}[/bold green]")
    console.print()

    # Try to render QR code
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
        console.print(f"  [dim](install qrcode for QR display: pip install qrcode)[/dim]")

    console.print(f"  3. You'll receive prayer times, sehri/iftar alerts on your phone.\n")
