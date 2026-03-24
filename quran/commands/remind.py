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


@app.command("setup")
def remind_setup():
    """Interactive wizard to configure all reminders (Prayers & Fasting)."""
    from quran.config.settings import load, save
    from rich.prompt import Confirm, IntPrompt
    import time
    
    cfg = load()
    
    console.print()
    console.print(Rule("[bold green]Reminder Setup Wizard[/bold green]"))
    console.print("  [dim]Let's configure your daily prayer and fasting notifications.[/dim]\n")
    
    # ── 1. Daily Prayers ──
    if Confirm.ask("  [1] Do you want [bold]5-times daily prayer[/bold] reminders?"):
        cfg["remind"]["fajr"] = True
        cfg["remind"]["dhuhr"] = True
        cfg["remind"]["asr"] = True
        cfg["remind"]["maghrib"] = True
        cfg["remind"]["isha"] = True
        
        console.print("  [dim]How many minutes before the Azan should we notify you?[/dim]")
        adv = IntPrompt.ask("  [dim]>[/dim] Advance warning minutes", default=cfg["remind"].get("advance_min", 10))
        cfg["remind"]["advance_min"] = adv
        
        adhan = Confirm.ask("  [dim]>[/dim] Play short Adhan sound on desktop notifications?", default=cfg["remind"].get("adhan_sound", True))
        cfg["remind"]["adhan_sound"] = adhan
    else:
        for p in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            cfg["remind"][p] = False

    console.print()
    
    # ── 2. Fasting Alerts ──
    if Confirm.ask("  [2] Do you want [bold]Daily Fasting (Sahur/Iftar)[/bold] alerts?"):
        sehri = Confirm.ask("  [dim]>[/dim] Enable Sahur (Sehri) countdown?", default=True)
        cfg["remind"]["fasting_sehri"] = sehri
        if sehri:
            s_min = IntPrompt.ask("     How many minutes before Sahur ends?", default=cfg["remind"].get("fasting_sehri_min", 30))
            cfg["remind"]["fasting_sehri_min"] = s_min
            
        iftar = Confirm.ask("  [dim]>[/dim] Enable Iftar alerts?", default=True)
        cfg["remind"]["fasting_iftar"] = iftar
        if iftar:
            i_min = IntPrompt.ask("     How many minutes before Iftar?", default=cfg["remind"].get("fasting_iftar_min", 10))
            cfg["remind"]["fasting_iftar_min"] = i_min
    else:
        cfg["remind"]["fasting_sehri"] = False
        cfg["remind"]["fasting_iftar"] = False

    save(cfg)
    console.print()
    console.print("  [green]✓ Settings saved![/green]")
    
    # ── 3. Start Daemon ──
    if Confirm.ask("\n  [3] Start the background reminder daemon now?", default=True):
        console.print()
        remind_on()
        
    # ── 4. Link Phone ──
    console.print()
    if Confirm.ask("  [4] Would you like to link your phone for cross-device notifications?", default=False):
        remind_phone()
    else:
        topic = cfg["remind"].get("phone_topic", "")
        if topic:
            console.print(f"  [dim]Phone already linked to ntfy.sh/{topic}[/dim]")
        else:
            console.print("  [dim]You can always link later using `quran remind phone`.[/dim]")
    
    console.print()
    console.print(Rule("[bold green]Setup Complete[/bold green]"))
    console.print()



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

    active_prayers = []
    for p in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
        if remind.get(p, True):
            active_prayers.append(p.capitalize())

    console.print(
        Panel(
            f"Daemon:    {status_s}\n"
            f"Phone:     {phone_s}\n"
            f"Goal:      [white]{remind.get('goal_ayahs', 5)} ayahs/day[/white]  "
            f"at [white]{remind.get('goal_time','20:00')}[/white]\n"
            f"Prayers:   [white]{', '.join(active_prayers) if active_prayers else 'None'}[/white]\n"
            f"Advance:   [white]{remind.get('advance_min', 10)} minutes prior[/white]\n"
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
    prayers:Annotated[Optional[str],typer.Option("--prayers", help="Comma-separated list (e.g. fajr,maghrib) or 'all' or 'none'")] = None,
    advance:Annotated[Optional[int],typer.Option("--advance", help="Minutes before prayer to notify (default 10)")] = None,
):
    """Set reading goal, reminder time, and prayer triggers."""
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

    if prayers is not None:
        all_p = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        val = prayers.lower().strip()
        if val == "none":
            for p in all_p:
                cfg["remind"][p] = False
            changed.append(f"prayers → [bold]none[/bold]")
        elif val == "all":
            for p in all_p:
                cfg["remind"][p] = True
            changed.append(f"prayers → [bold]all[/bold]")
        else:
            selected = [p.strip() for p in val.split(",")]
            for p in all_p:
                cfg["remind"][p] = p in selected
            changed.append(f"prayers → [bold]{', '.join([p for p in all_p if p in selected])}[/bold]")

    if advance is not None:
        cfg["remind"]["advance_min"] = advance
        changed.append(f"advance → [bold]{advance} minutes[/bold]")

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
@app.command("test")
def remind_test():
    """Send a test notification to all configured channels (Desktop, Telegram, etc)."""
    from quran.connectors.connectors import dispatch
    from quran.config.settings import load

    cfg = load()
    city = cfg.get("location", {}).get("city", "your city")
    
    console.print("[dim]Sending test notification to all enabled channels…[/dim]")
    topic = cfg["remind"].get("phone_topic", "")
    dispatch("🕌 quran-cli Test", f"This is a test reminder from your terminal. Location: {city}", topic=topic)
    console.print("[green]✓[/green] Test notification dispatched.")
