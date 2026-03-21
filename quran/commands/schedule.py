"""
quran schedule — full day Islamic schedule view.

Usage:
  quran schedule
  quran schedule --week
  quran schedule --date 2026-03-25
"""
from __future__ import annotations
from datetime import datetime, timedelta, date
import typer
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Full-day Islamic schedule.")
console = Console()


@app.callback(invoke_without_command=True)
def schedule_cmd(
    ctx:   typer.Context,
    week:  Annotated[bool,         typer.Option("--week",  "-w", help="Show 7-day timetable")] = False,
    date_: Annotated[Optional[str], typer.Option("--date",  "-d", help="Date YYYY-MM-DD")] = None,
):
    if ctx.invoked_subcommand:
        return

    from quran.config.settings import load
    from quran.core.location import detect_location
    from quran.core.prayer_times import get_prayer_times, sehri_time
    from quran.core.ramadan import is_ramadan, ramadan_day
    from quran.ui.renderer import print_location_header

    cfg = load()
    loc = detect_location()
    ram = is_ramadan()

    if week:
        _show_week(loc, cfg, ram)
        return

    for_date = date.fromisoformat(date_) if date_ else date.today()
    pt       = get_prayer_times(
        loc["lat"], loc["lon"], for_date=for_date,
        method=cfg.get("method","Karachi"),
        asr_method=cfg.get("asr_method","Standard"),
        tz=loc.get("tz",""),
    )

    print_location_header(loc, ram)
    console.print(f"  [dim]{for_date.strftime('%A, %d %B %Y')}[/dim]")

    if ram:
        rd = ramadan_day(for_date)
        console.print(f"  [yellow]☽ Ramadan day {rd}[/yellow]")

    console.print()

    now   = datetime.now()
    times = _build_rows(pt, now, ram)

    _render_schedule(times, now)

    # Fast duration
    if ram:
        sehri = sehri_time(pt)
        iftar = pt.maghrib
        duration = iftar - sehri
        h = int(duration.total_seconds() // 3600)
        m = int((duration.total_seconds() % 3600) // 60)
        console.print(f"\n  [dim]Fast duration: [bold yellow]{h}h {m:02d}m[/bold yellow]  "
                      f"({sehri.strftime('%I:%M %p')} → {iftar.strftime('%I:%M %p')})[/dim]")

    console.print(f"\n  [dim]Method: {cfg.get('method','?')}  ·  run [green]quran pray next[/green] for countdown[/dim]\n")


def _build_rows(pt, now: datetime, ram: bool) -> list[dict]:
    from quran.core.prayer_times import sehri_time

    rows = []

    if ram:
        sehri = sehri_time(pt)
        rows.append({"name": "Sehri",   "dt": sehri,    "special": True,  "ramadan": True})
    rows.append({"name": "Fajr",    "dt": pt.fajr,    "special": False, "ramadan": False})
    rows.append({"name": "Sunrise", "dt": pt.sunrise, "special": False, "ramadan": False, "dim": True})
    rows.append({"name": "Dhuhr",   "dt": pt.dhuhr,   "special": False, "ramadan": False})
    rows.append({"name": "Asr",     "dt": pt.asr,     "special": False, "ramadan": False})
    if ram:
        rows.append({"name": "Iftar",   "dt": pt.maghrib, "special": True,  "ramadan": True})
    rows.append({"name": "Maghrib", "dt": pt.maghrib, "special": False, "ramadan": False})
    rows.append({"name": "Isha",    "dt": pt.isha,    "special": False, "ramadan": False})
    if ram:
        tarawih = pt.isha.replace(hour=(pt.isha.hour + 1) % 24, minute=30)
        rows.append({"name": "Tarawih", "dt": tarawih,  "special": True,  "ramadan": True})

    # Assign status
    for r in rows:
        if r["dt"] < now:
            r["status"] = "done"
            r["pct"]    = 100
        else:
            r["status"] = "open"
            r["pct"]    = 0

    return rows


def _render_schedule(rows: list[dict], now: datetime) -> None:
    from quran.ui.renderer import render_schedule_table
    from datetime import timedelta

    sorted_rows = sorted(rows, key=lambda x: x["dt"])
    
    # Identify the chronologically next event today
    next_event = None
    for r in sorted_rows:
        if r["dt"] > now:
            next_event = r
            break
            
    prev_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # If all events today have passed, the next event is tomorrow's very first event
    if not next_event:
        next_event = sorted_rows[0]
        target_dt = next_event["dt"] + timedelta(days=1)
        prev_dt = sorted_rows[-1]["dt"]  # Last event of today (usually Isha or Tarawih)
    else:
        target_dt = next_event["dt"]
        for r in reversed(sorted_rows):
            if r["dt"] <= now:
                prev_dt = r["dt"]
                break

    for r in rows:
        if r["name"] == next_event["name"]:
            r["status"] = "next"
            total = (target_dt - prev_dt).total_seconds()
            elapsed = (now - prev_dt).total_seconds()
            if total > 0:
                r["pct"] = min(100, max(0, int((elapsed / total) * 100)))
            else:
                r["pct"] = 0
            break
            
    render_schedule_table(rows)


def _show_week(loc: dict, cfg: dict, ram: bool) -> None:
    from quran.core.prayer_times import get_prayer_times, sehri_time

    table = Table(
        box=box.SIMPLE_HEAD, show_header=True,
        header_style="dim", border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("Day",      style="dim", width=11)
    table.add_column("Fajr",     width=9)
    table.add_column("Dhuhr",    width=9)
    table.add_column("Asr",      width=9)
    table.add_column("Maghrib",  width=9)
    table.add_column("Isha",     width=9)
    if ram:
        table.add_column("Sehri",   style="yellow", width=9)
        table.add_column("Iftar",   style="yellow", width=9)

    today = date.today()
    for i in range(7):
        d  = today + timedelta(days=i)
        pt = get_prayer_times(
            loc["lat"], loc["lon"], for_date=d,
            method=cfg.get("method","Karachi"),
            asr_method=cfg.get("asr_method","Standard"),
            tz=loc.get("tz",""),
        )
        day_s = ("[bold green]Today[/bold green]" if i == 0
                 else f"[dim]{d.strftime('%a %d')}"
                      f"{'[/dim]' if i > 0 else ''}")
        row = [
            day_s,
            pt.fajr.strftime("%I:%M"),
            pt.dhuhr.strftime("%I:%M"),
            pt.asr.strftime("%I:%M"),
            pt.maghrib.strftime("%I:%M"),
            pt.isha.strftime("%I:%M"),
        ]
        if ram:
            row += [
                sehri_time(pt).strftime("%I:%M"),
                pt.maghrib.strftime("%I:%M"),
            ]
        table.add_row(*row)

    console.print()
    console.print(f"  [dim]7-day timetable — {loc.get('city','?')}, {loc.get('country','?')}[/dim]\n")
    console.print(table)
    console.print(f"  [dim]Method: {cfg.get('method','?')}[/dim]\n")
