"""
quran ramadan — Ramadan timings, month calendar, fast tracker.

Usage:
  quran ramadan              # today's sehri, iftar, tarawih
  quran ramadan --week       # 7-day table
  quran ramadan --month      # full 30-day calendar
  quran ramadan --notify     # enable 15-min sehri/iftar alerts
"""
from __future__ import annotations
from datetime import date, timedelta
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box
from typing_extensions import Annotated

app     = typer.Typer(help="Ramadan timings and calendar.")
console = Console()


def _get_deps():
    from quran.config.settings import load
    from quran.core.location import detect_location
    from quran.core.prayer_times import get_prayer_times, sehri_time
    from quran.core.ramadan import (is_ramadan, ramadan_day, ramadan_year,
                                     monthly_timetable, LAYLATUL_QADR_NIGHTS,
                                     days_until_ramadan)
    cfg  = load()
    loc  = detect_location()
    return cfg, loc


@app.callback(invoke_without_command=True)
def ramadan_cmd(
    ctx:    typer.Context,
    week:   Annotated[bool, typer.Option("--week",   help="Show 7-day table")] = False,
    month:  Annotated[bool, typer.Option("--month",  help="Full 30-day calendar")] = False,
    notify: Annotated[bool, typer.Option("--notify", help="Enable sehri/iftar push alerts")] = False,
    fast:   Annotated[bool, typer.Option("--fast",   help="Mark today's fast as complete")] = False,
):
    if ctx.invoked_subcommand:
        return

    from quran.core.ramadan import is_ramadan, ramadan_day, ramadan_year, days_until_ramadan

    cfg, loc = _get_deps()

    if fast:
        from quran.core.streak import mark_fast
        fd = mark_fast()
        console.print(f"[green]✓[/green] Fast recorded. Streak: [bold green]{fd['current']}[/bold green] days  "
                      f"Best: [dim]{fd['best']}[/dim]")
        return

    if notify:
        _setup_notify(cfg)
        return

    if not is_ramadan():
        days = days_until_ramadan()
        hy   = ramadan_year()
        if days is not None and days > 0:
            console.print(f"\n  [yellow]☽[/yellow] Ramadan {hy + 1} begins in "
                          f"[bold yellow]{days}[/bold yellow] days\n")
        else:
            console.print(f"\n  [dim]Not currently Ramadan.[/dim]\n")
        return

    if month:
        _show_month(cfg, loc)
    elif week:
        _show_week(cfg, loc)
    else:
        _show_today(cfg, loc)


def _show_today(cfg: dict, loc: dict) -> None:
    from quran.core.prayer_times import get_prayer_times, sehri_time
    from quran.core.ramadan import (ramadan_day, ramadan_year, LAYLATUL_QADR_NIGHTS,
                                     ramadan_end_date, ramadan_start_date)
    from quran.ui.renderer import print_location_header

    pt      = get_prayer_times(
        loc["lat"], loc["lon"],
        method=cfg.get("method","Karachi"),
        asr_method=cfg.get("asr_method","Standard"),
        tz=loc.get("tz",""),
    )
    sehri   = sehri_time(pt)
    iftar   = pt.maghrib
    tarawih = pt.isha.replace(hour=(pt.isha.hour+1)%24, minute=30)
    rd      = ramadan_day()
    hy      = ramadan_year()

    import datetime as _dt
    now    = _dt.datetime.now()
    dur    = iftar - sehri
    dur_h  = dur.total_seconds() / 3600
    pct_done = min(100, max(0, int(
        (now - sehri).total_seconds() / dur.total_seconds() * 100
    ))) if sehri < now < iftar else (100 if now >= iftar else 0)

    print_location_header(loc, is_ramadan=True)

    console.print(
        Panel(
            f"[yellow]☽ Ramadan {hy}[/yellow]  [dim]Day[/dim] [bold yellow]{rd}[/bold yellow] [dim]of 30[/dim]\n",
            border_style="yellow", padding=(0, 2)
        )
    )
    console.print()

    table = Table(box=box.SIMPLE, show_header=False, padding=(0,2), border_style="bright_black")
    table.add_column("Label",  style="dim",    width=14)
    table.add_column("Time",   style="white",  width=12)
    table.add_column("Note",   style="",       width=24)

    from quran.ui.renderer import countdown_str

    def _status(dt) -> str:
        if dt > now:
            return f"[green]in {countdown_str(dt)}[/green]"
        return "[dim]done[/dim]"

    table.add_row("Sehri ends", sehri.strftime("%I:%M %p"),   _status(sehri))
    table.add_row("Fajr",       pt.fajr.strftime("%I:%M %p"), _status(pt.fajr))
    table.add_row("Dhuhr",      pt.dhuhr.strftime("%I:%M %p"), "[dim]—[/dim]")
    table.add_row("Asr",        pt.asr.strftime("%I:%M %p"),  "[dim]—[/dim]")
    table.add_row("[yellow]Iftar[/yellow]",
                  f"[yellow]{iftar.strftime('%I:%M %p')}[/yellow]", _status(iftar))
    table.add_row("Maghrib",    pt.maghrib.strftime("%I:%M %p"), "[dim]—[/dim]")
    table.add_row("Isha",       pt.isha.strftime("%I:%M %p"), "[dim]—[/dim]")
    table.add_row("[dim]Tarawih[/dim]",
                  f"[dim]{tarawih.strftime('%I:%M %p')}[/dim]", "[dim]optional[/dim]")
    console.print(table)

    # Fast progress bar
    bar_w  = 28
    filled = int(bar_w * pct_done / 100)
    bar    = "[yellow]" + "█" * filled + "[/yellow]" + "[bright_black]" + "░" * (bar_w - filled) + "[/bright_black]"
    console.print(f"\n  Fast duration: [bold]{dur_h:.1f}h[/bold]  [{bar}] [dim]{pct_done}%[/dim]")

    # Laylatul Qadr notice
    if rd in LAYLATUL_QADR_NIGHTS:
        console.print(f"\n  [bold yellow]★[/bold yellow] [yellow]Tonight may be Laylatul Qadr — increase your worship.[/yellow]")
    elif rd > 20:
        nights_left = [n for n in LAYLATUL_QADR_NIGHTS if n >= rd]
        if nights_left:
            console.print(f"\n  [dim]Seek Laylatul Qadr on nights: {', '.join(str(n) for n in nights_left)}[/dim]")

    console.print(f"\n  [dim]run [green]quran ramadan --month[/green] for full calendar[/dim]\n")


def _show_week(cfg: dict, loc: dict) -> None:
    from quran.core.prayer_times import get_prayer_times, sehri_time
    from quran.core.ramadan import ramadan_day

    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style="dim", border_style="bright_black", padding=(0,1))
    table.add_column("Day",    width=10)
    table.add_column("Sehri",  style="yellow", width=9)
    table.add_column("Fajr",   width=9)
    table.add_column("Iftar",  style="yellow", width=9)
    table.add_column("Maghrib",width=9)
    table.add_column("Isha",   width=9)
    table.add_column("Fast",   style="dim",    width=7)

    today = date.today()
    for i in range(7):
        d  = today + timedelta(days=i)
        pt = get_prayer_times(
            loc["lat"], loc["lon"], for_date=d,
            method=cfg.get("method","Karachi"),
            asr_method=cfg.get("asr_method","Standard"),
            tz=loc.get("tz",""),
        )
        sehri = sehri_time(pt)
        dur_h = (pt.maghrib - sehri).total_seconds() / 3600
        rd    = ramadan_day(d)
        label = ("[bold green]Today[/bold green]" if i == 0
                 else f"[dim]{d.strftime('%a %d')}[/dim]")
        if rd:
            label += f" [dim]#{rd}[/dim]"
        table.add_row(
            label,
            sehri.strftime("%I:%M"),
            pt.fajr.strftime("%I:%M"),
            pt.maghrib.strftime("%I:%M"),
            pt.maghrib.strftime("%I:%M"),
            pt.isha.strftime("%I:%M"),
            f"{dur_h:.1f}h",
        )

    console.print(f"\n  [yellow]☽ Ramadan — 7-day timetable[/yellow]  [dim]{loc.get('city','?')}[/dim]\n")
    console.print(table)


def _show_month(cfg: dict, loc: dict) -> None:
    from quran.core.ramadan import monthly_timetable, ramadan_year

    hy   = ramadan_year()
    with console.status(f"[dim]Computing Ramadan {hy} calendar…[/dim]"):
        rows = monthly_timetable(
            loc["lat"], loc["lon"], hijri_year=hy,
            method=cfg.get("method","Karachi"),
            asr_method=cfg.get("asr_method","Standard"),
        )

    if not rows:
        console.print("[red]✗[/red] Could not compute monthly timetable.")
        return

    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style="dim", border_style="bright_black", padding=(0,1))
    table.add_column("#",      width=4)
    table.add_column("Date",   width=9,  style="dim")
    table.add_column("Sehri",  width=8,  style="yellow")
    table.add_column("Iftar",  width=8,  style="yellow")
    table.add_column("Fajr",   width=8)
    table.add_column("Isha",   width=8)
    table.add_column("Fast",   width=6,  style="dim")

    today = date.today()
    for r in rows:
        is_today = r["date"] == today
        day_s = f"[bold green]{r['day']:>2}[/bold green]" if is_today else f"{r['day']:>2}"
        date_s = r["date"].strftime("%d %b")
        table.add_row(
            day_s, date_s,
            r["sehri"].strftime("%H:%M"),
            r["iftar"].strftime("%H:%M"),
            r["fajr"].strftime("%H:%M"),
            r["isha"].strftime("%H:%M"),
            f"{r['fast_duration_h']:.1f}h",
        )

    console.print(f"\n  [yellow]☽ Ramadan {hy}[/yellow]  [dim]{loc.get('city','?')}, {loc.get('country','?')}[/dim]\n")
    console.print(table)
    console.print(f"  [dim]Method: {cfg.get('method','?')}[/dim]\n")


def _setup_notify(cfg: dict) -> None:
    from quran.config.settings import save
    smin = cfg.get("ramadan", {}).get("notify_sehri_min", 15)
    imin = cfg.get("ramadan", {}).get("notify_iftar_min", 15)
    console.print(f"[green]✓[/green] Sehri warning: [bold]{smin} min[/bold] before end")
    console.print(f"[green]✓[/green] Iftar alert:   [bold]{imin} min[/bold] before Maghrib")
    console.print()
    console.print(f"[dim]Change: [green]quran config set ramadan.notify_sehri_min 10[/green][/dim]")
    console.print(f"[dim]Start daemon: [green]quran remind on[/green][/dim]\n")
