"""
quran lock — terminal screen lock with optional PIN protection.

Usage:
  quran lock          # lock the screen immediately
  quran lock setup    # set or change your PIN
  quran lock off      # remove PIN and disable lock
"""
from __future__ import annotations
import hashlib
import getpass
import time
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.rule import Rule
import typer

app     = typer.Typer(help="Screen lock with optional PIN protection.")
console = Console()

WAQT = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
WAQT_AR = {
    "Fajr":    "الفجر",
    "Dhuhr":   "الظهر",
    "Asr":     "العصر",
    "Maghrib": "المغرب",
    "Isha":    "العشاء",
}


# ── PIN helpers ───────────────────────────────────────────────────────────────

def _hash(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def _get_pin_hash() -> str:
    from quran.config.settings import load
    return load().get("lock", {}).get("pin_hash", "")


def _save_pin(pin: str | None) -> None:
    from quran.config.settings import load, save
    cfg = load()
    cfg.setdefault("lock", {})
    if pin:
        cfg["lock"]["pin_hash"] = _hash(pin)
        cfg["lock"]["enabled"]  = True
    else:
        cfg["lock"]["pin_hash"] = ""
        cfg["lock"]["enabled"]  = False
    save(cfg)


# ── Context loader ────────────────────────────────────────────────────────────

def _load_context():
    from quran.config.settings import load
    from quran.core.location import detect_location
    from quran.core.prayer_times import get_prayer_times
    from quran.core.ramadan import gregorian_to_hijri, is_ramadan

    cfg   = load()
    loc   = detect_location()
    today = datetime.now().date()
    pt    = get_prayer_times(
        float(loc["lat"]),
        float(loc["lon"]),
        for_date=today,
        method=cfg.get("method", "Karachi"),
        asr_method=cfg.get("asr_method", "Standard"),
        tz=loc.get("tz", ""),
    )
    hy, hm, hd = gregorian_to_hijri(today)
    months = [
        "Muharram", "Safar", "Rabi Al-Awwal", "Rabi Al-Thani",
        "Jumada Al-Awwal", "Jumada Al-Thani", "Rajab", "Sha'aban",
        "Ramadan", "Shawwal", "Dhul-Qi'dah", "Dhul-Hijjah",
    ]
    hijri   = f"{hd} {months[hm - 1]} {hy} AH"
    city    = loc.get("city", "Unknown")
    country = loc.get("country", "")
    return pt, city, country, hijri, is_ramadan()


# ── Lock screen builder ───────────────────────────────────────────────────────

def _build_lock_screen(pt, city: str, country: str, hijri: str, is_ram: bool) -> Panel:
    from quran.core.prayer_times import sehri_time, iftar_time

    now             = datetime.now()
    times           = pt.as_dict()
    next_name, next_dt = pt.next_prayer(now)

    diff  = next_dt.replace(tzinfo=None) - now.replace(tzinfo=None)
    total = max(0, int(diff.total_seconds()))
    h, r  = divmod(total, 3600)
    m, s  = divmod(r, 60)
    cd    = f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"

    body = Text(justify="center")
    body.append("بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ\n\n", style="bold yellow")
    body.append(now.strftime("%H:%M:%S"),                    style="bold green")
    body.append(f"\n{now.strftime('%A, %d %B %Y')}",         style="white")
    body.append(f"\n{hijri}\n\n",                            style="dim white")
    body.append(f"{city}, {country}",                        style="dim")
    if is_ram:
        body.append("  ·  ☽ Ramadan Mubarak",               style="yellow")
    body.append(f"\n\nNext:  {next_name}  ·  in  {cd}\n\n", style="bold green")

    for pname in WAQT:
        dt = times.get(pname)
        if dt is None:
            continue
        t_str   = dt.strftime("%I:%M %p")
        is_next = pname == next_name
        is_done = dt.replace(tzinfo=None) < now.replace(tzinfo=None)
        ar_name = WAQT_AR.get(pname, "")
        marker  = "▶" if is_next else " "

        if is_next:
            body.append(f"  {marker}  {pname:<10}{ar_name:<10}  {t_str}\n", style="bold green")
        elif is_done:
            body.append(f"  {marker}  {pname:<10}{ar_name:<10}  {t_str}\n", style="dim")
        else:
            body.append(f"  {marker}  {pname:<10}{ar_name:<10}  {t_str}\n", style="white")

    if is_ram:
        sh  = sehri_time(pt).strftime("%I:%M %p")
        ift = iftar_time(pt).strftime("%I:%M %p")
        body.append(f"\n  Sehri: {sh}  ·  Iftar: {ift}", style="yellow")

    body.append("\n\n  🔒  Screen Locked  ·  Enter PIN to unlock", style="dim")

    return Panel(
        Align.center(body),
        title="[dim]  quran-cli  ·  Screen Locked  [/dim]",
        subtitle="[dim]  Ctrl+C to force quit  [/dim]",
        border_style="green",
        padding=(2, 10),
    )


# ── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def lock_cmd(ctx: typer.Context):
    """Lock the screen. Requires PIN to unlock if configured."""
    if ctx.invoked_subcommand:
        return

    pin_hash = _get_pin_hash()

    console.print()
    with console.status("[dim]Loading…[/dim]"):
        try:
            pt, city, country, hijri, is_ram = _load_context()
        except Exception as e:
            console.print(f"  [red]Error:[/red] {e}")
            return

    if not pin_hash:
        # No PIN — live lock screen, Ctrl+C to exit
        console.print(
            "  [dim]No PIN set. Use [green]quran lock setup[/green] "
            "to add one. Press Ctrl+C to exit.[/dim]\n"
        )
        time.sleep(1.2)
        try:
            try:
                with Live(console=console, refresh_per_second=1, screen=True) as live:
                    while True:
                        live.update(_build_lock_screen(pt, city, country, hijri, is_ram))
                        time.sleep(1)
            except Exception:
                # Fallback for terminals that don't support alternate screen
                with Live(console=console, refresh_per_second=1, screen=False) as live:
                    while True:
                        live.update(_build_lock_screen(pt, city, country, hijri, is_ram))
                        time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    # PIN required — static snapshot then prompt
    attempts = 0
    while True:
        console.clear()
        console.print(_build_lock_screen(pt, city, country, hijri, is_ram))
        try:
            entered = getpass.getpass("\n  PIN: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.clear()
            console.print(
                "  [dim]Screen still locked. "
                "Run [green]quran lock[/green] again to unlock.[/dim]\n"
            )
            return

        if _hash(entered) == pin_hash:
            console.clear()
            console.print("  [green]✓[/green] Unlocked.\n")
            return

        attempts += 1
        console.print(f"  [red]✗[/red] Incorrect PIN.  [dim](attempt {attempts})[/dim]")
        time.sleep(1.5)


@app.command("setup")
def lock_setup():
    """Set or change the screen lock PIN."""
    console.print()
    console.print(Rule("[dim]Screen Lock Setup[/dim]", style="green"))
    console.print()
    console.print("  [dim]Set a PIN to protect your terminal screen.[/dim]")
    console.print("  [dim]Leave blank to use Ctrl+C-only lock (no PIN required).[/dim]\n")

    try:
        pin1 = getpass.getpass("  New PIN (blank to disable): ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n  [dim]Cancelled.[/dim]")
        return

    if not pin1:
        _save_pin(None)
        console.print("  [green]✓[/green] PIN disabled. Ctrl+C exits the lock screen.\n")
        return

    try:
        pin2 = getpass.getpass("  Confirm PIN: ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n  [dim]Cancelled.[/dim]")
        return

    if pin1 != pin2:
        console.print("  [red]✗[/red] PINs do not match. Try again.")
        return

    _save_pin(pin1)
    console.print(
        "  [green]✓[/green] PIN saved. "
        "Run [bold green]quran lock[/bold green] to lock your screen.\n"
    )


@app.command("off")
def lock_off():
    """Remove the screen lock PIN."""
    _save_pin(None)
    console.print("  [green]✓[/green] Screen lock PIN removed.\n")
