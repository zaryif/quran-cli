"""
quran pray — prayer times for your auto-detected or configured location.

Usage:
  quran pray              # today's 5 times
  quran pray next         # countdown to next prayer
  quran pray setup        # interactive location + method setup
"""
from __future__ import annotations
from datetime import datetime
import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from typing_extensions import Annotated

app     = typer.Typer(help="Prayer times for your location.")
console = Console()


def _get_times():
    from quran.config.settings import load
    from quran.core.location import detect_location
    from quran.core.prayer_times import get_prayer_times

    cfg = load()
    loc = detect_location()
    pt  = get_prayer_times(
        loc["lat"], loc["lon"],
        method=cfg.get("method", "Karachi"),
        asr_method=cfg.get("asr_method", "Standard"),
        tz=loc.get("tz", ""),
    )
    return pt, loc, cfg


@app.callback(invoke_without_command=True)
def pray_cmd(ctx: typer.Context):
    """Show today's prayer times."""
    if ctx.invoked_subcommand:
        return
    _show_times()


@app.command("next")
def pray_next():
    """Countdown to the next prayer."""
    pt, loc, cfg = _get_times()
    name, dt     = pt.next_prayer()
    from quran.ui.renderer import countdown_str, print_location_header
    from quran.core.ramadan import is_ramadan

    print_location_header(loc, is_ramadan())
    remaining = countdown_str(dt)
    console.print(
        Panel(
            f"[bold green]{name}[/bold green]\n"
            f"[white]{dt.strftime('%I:%M %p')}[/white]\n\n"
            f"[dim]in [bold green]{remaining}[/bold green][/dim]",
            title="[dim]next prayer[/dim]",
            border_style="green",
            padding=(1, 4),
        )
    )


@app.command("setup")
def pray_setup():
    """Interactive location & calculation method setup."""
    from quran.config.settings import load, save
    from quran.core.prayer_times import METHODS

    console.print(Rule("[dim]quran pray setup[/dim]", style="green"))
    console.print()

    cfg = load()

    # Location
    console.print("[dim]Auto-detect location from IP? (Y/n):[/dim] ", end="")
    choice = input().strip().lower()
    if choice in ("", "y", "yes"):
        from quran.core.location import detect_location
        with console.status("[dim]Detecting location…[/dim]"):
            loc = detect_location(force=True)
        console.print(f"[green]✓[/green] Detected: [bold]{loc['city']}, {loc['country']}[/bold]")
        cfg["location"] = loc
    else:
        console.print("[dim]City name:[/dim] ", end="")
        city = input().strip()
        console.print("[dim]Latitude:[/dim] ", end="")
        lat = float(input().strip())
        console.print("[dim]Longitude:[/dim] ", end="")
        lon = float(input().strip())
        console.print("[dim]Timezone (e.g. Asia/Dhaka):[/dim] ", end="")
        tz  = input().strip()
        cfg["location"] = {"city": city, "lat": lat, "lon": lon, "tz": tz, "auto": False}

    # Method
    console.print()
    console.print("[dim]Calculation method:[/dim]")
    methods = list(METHODS.keys())
    for i, m in enumerate(methods, 1):
        marker = "[green]✓[/green] " if m == cfg.get("method") else "  "
        console.print(f"  {marker}{i}. {m}  [dim]{METHODS[m]['name']}[/dim]")
    console.print(f"[dim]Choose (1-{len(methods)}):[/dim] ", end="")
    try:
        idx = int(input().strip()) - 1
        cfg["method"] = methods[idx]
        console.print(f"[green]✓[/green] Method set to [bold]{methods[idx]}[/bold]")
    except (ValueError, IndexError):
        console.print("[dim]Keeping current method.[/dim]")

    # Asr
    console.print()
    console.print("[dim]Asr method: (1) Standard/Shafi  (2) Hanafi:[/dim] ", end="")
    asr_choice = input().strip()
    cfg["asr_method"] = "Hanafi" if asr_choice == "2" else "Standard"
    console.print(f"[green]✓[/green] Asr method: [bold]{cfg['asr_method']}[/bold]")

    save(cfg)
    console.print()
    console.print("[green]✓[/green] Configuration saved.")
    _show_times()


def _show_times():
    pt, loc, cfg = _get_times()
    from quran.ui.renderer import render_prayer_table, print_location_header
    from quran.core.ramadan import is_ramadan, is_ramadan as _ir
    from quran.core.prayer_times import sehri_time, iftar_time

    ram = is_ramadan()
    print_location_header(loc, ram)

    now        = datetime.now()
    next_name, _= pt.next_prayer(now)

    extras = {}
    if ram:
        extras["Sehri"]   = sehri_time(pt)
        extras["Iftar"]   = iftar_time(pt)
        extras["Tarawih"] = pt.isha.replace(hour=(pt.isha.hour + 1) % 24, minute=30)

    render_prayer_table(pt.as_dict(), next_name=next_name, extras=extras if ram else None)

    method = cfg.get("method", "Karachi")
    console.print(f"[dim]  Method: {method}  ·  {now.strftime('%A, %d %B %Y')}[/dim]\n")
