"""
quran fasting — daily fasting times (Sahur & Iftar) for any day of the year.

Shows fasting times based on your location's Fajr and Maghrib times.
Highlights Sunnah fasting days: Monday, Thursday, White Days (13-15 Hijri),
Day of Arafah, Ashura, and Sha'ban fasting.

Usage:
  quran fasting                   # today's fasting times
  quran fasting --week            # 7-day sehri/iftar table
  quran fasting --date 2026-04-01 # specific date
"""
from __future__ import annotations
from datetime import date, timedelta, datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box
from typing_extensions import Annotated

app     = typer.Typer(help="Daily fasting times — Sahur, Iftar & Sunnah days.")
console = Console()


# ── Sunnah fasting calendar ──────────────────────────────────────────────────

SUNNAH_WEEKDAYS = {0, 3}  # Monday=0, Thursday=3

WHITE_DAYS = {13, 14, 15}  # 13th, 14th, 15th of every Hijri month


def _sunnah_label(d: date) -> str:
    """Return Sunnah fasting label for a Gregorian date, if any."""
    from quran.core.ramadan import gregorian_to_hijri
    labels = []

    # Monday/Thursday
    if d.weekday() == 0:
        labels.append("Monday (Sunnah)")
    elif d.weekday() == 3:
        labels.append("Thursday (Sunnah)")

    # White days (Ayyam al-Bid)
    try:
        _, hm, hd = gregorian_to_hijri(d)
        if hd in WHITE_DAYS:
            labels.append(f"White Day ({hd} Hijri)")
        # Day of Arafah (9 Dhul Hijjah)
        if hm == 12 and hd == 9:
            labels.append("Day of Arafah ★")
        # Ashura (10 Muharram)
        if hm == 1 and hd == 10:
            labels.append("Ashura (10 Muharram)")
        # 6 days of Shawwal
        if hm == 10 and 2 <= hd <= 7:
            labels.append("Shawwal Sunnah")
    except Exception:
        pass

    return " · ".join(labels) if labels else ""


def _get_fasting_times(d: date) -> dict:
    """Get sahur (end) and iftar times for a given date."""
    from quran.config.settings import load
    from quran.core.location import detect_location
    from quran.core.prayer_times import get_prayer_times, sehri_time

    cfg = load()
    loc = detect_location()
    pt  = get_prayer_times(
        loc["lat"], loc["lon"],
        for_date=d,
        method=cfg.get("method", "Karachi"),
        asr_method=cfg.get("asr_method", "Standard"),
        tz=loc.get("tz", ""),
    )
    sahur = sehri_time(pt)
    iftar = pt.maghrib

    dur = iftar - sahur
    dur_h = dur.total_seconds() / 3600

    return {
        "date":     d,
        "sahur":    sahur,
        "fajr":     pt.fajr,
        "iftar":    iftar,
        "duration": dur_h,
        "location": loc,
        "sunnah":   _sunnah_label(d),
    }


# ── Commands ─────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def fasting_cmd(
    ctx:  typer.Context,
    week: Annotated[bool, typer.Option("--week", help="Show 7-day table")] = False,
    dt:   Annotated[str,  typer.Option("--date", help="Date (YYYY-MM-DD)")] = "",
):
    """Show daily fasting times (Sahur & Iftar) for any day."""
    if ctx.invoked_subcommand:
        return

    if week:
        _show_week()
        return

    target = date.today()
    if dt:
        try:
            target = date.fromisoformat(dt)
        except ValueError:
            console.print(f"[red]✗[/red] Invalid date: {dt}. Use YYYY-MM-DD.")
            return

    _show_today(target)


def _show_today(d: date) -> None:
    """Display fasting times for a single day."""
    from quran.core.ramadan import gregorian_to_hijri, is_ramadan

    with console.status("[dim]Calculating fasting times…[/dim]"):
        info = _get_fasting_times(d)

    loc    = info["location"]
    sahur  = info["sahur"]
    iftar  = info["iftar"]
    dur_h  = info["duration"]
    sunnah = info["sunnah"]

    # Hijri date
    try:
        hy, hm, hd = gregorian_to_hijri(d)
        hijri_months = [
            "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
            "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Sha'ban",
            "Ramadan", "Shawwal", "Dhul Qi'dah", "Dhul Hijjah"
        ]
        hm_name = hijri_months[hm - 1] if 1 <= hm <= 12 else str(hm)
        hijri_str = f"{hd} {hm_name} {hy} AH"
    except Exception:
        hijri_str = ""

    console.print()
    console.print(Rule(
        f"[bold]Fasting Times[/bold]  [dim]{d.strftime('%A, %d %B %Y')}[/dim]",
        style="green"
    ))
    console.print()

    if hijri_str:
        console.print(f"  [dim]Hijri:[/dim] [yellow]{hijri_str}[/yellow]")
    console.print(f"  [dim]Location:[/dim] {loc.get('city', '?')}, {loc.get('country', '')}")
    console.print()

    # Sahur & Iftar panel
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2),
                  border_style="bright_black")
    table.add_column("", width=15, style="dim")
    table.add_column("", width=12, style="bold")
    table.add_column("", width=30)

    now = datetime.now()

    def _status(dt_val) -> str:
        if dt_val > now:
            delta = dt_val - now
            h, m = divmod(int(delta.total_seconds()) // 60, 60)
            return f"[green]in {h}h {m}m[/green]"
        return "[dim]passed[/dim]"

    table.add_row("Sahur ends",  sahur.strftime("%I:%M %p"), _status(sahur))
    table.add_row("Fajr",        info["fajr"].strftime("%I:%M %p"), "[dim]prayer begins[/dim]")
    table.add_row("[yellow]Iftar[/yellow]",
                  f"[yellow]{iftar.strftime('%I:%M %p')}[/yellow]", _status(iftar))

    console.print(table)
    console.print(f"\n  [dim]Duration:[/dim] [bold]{dur_h:.1f} hours[/bold]")

    # Sunnah notice
    if sunnah:
        console.print(f"\n  [green]★[/green] [green]{sunnah}[/green]")

    # If it's Ramadan, point to the ramadan command
    if is_ramadan():
        console.print(f"\n  [yellow]☽[/yellow] [dim]It's Ramadan! Use [green]quran ramadan[/green] for full schedule.[/dim]")

    # Upcoming Sunnah days
    _show_upcoming_sunnah(d)
    console.print()


def _show_upcoming_sunnah(from_date: date) -> None:
    """Show next few Sunnah fasting days."""
    upcoming = []
    for i in range(1, 15):
        d = from_date + timedelta(days=i)
        label = _sunnah_label(d)
        if label:
            upcoming.append((d, label))
        if len(upcoming) >= 3:
            break

    if upcoming:
        console.print(f"\n  [dim]Upcoming Sunnah fasts:[/dim]")
        for d, label in upcoming:
            console.print(f"    [dim]{d.strftime('%a %d %b')}[/dim]  {label}")


def _show_week() -> None:
    """Show 7-day fasting times table."""
    today = date.today()

    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style="dim", border_style="bright_black", padding=(0, 1))
    table.add_column("Day",      width=12)
    table.add_column("Sahur",    width=9, style="yellow")
    table.add_column("Iftar",    width=9, style="yellow")
    table.add_column("Duration", width=7, style="dim")
    table.add_column("Sunnah",   width=25, style="green")

    for i in range(7):
        d    = today + timedelta(days=i)
        info = _get_fasting_times(d)
        label = "[bold green]Today[/bold green]" if i == 0 else f"[dim]{d.strftime('%a %d')}[/dim]"

        table.add_row(
            label,
            info["sahur"].strftime("%I:%M"),
            info["iftar"].strftime("%I:%M"),
            f"{info['duration']:.1f}h",
            info["sunnah"] or "[dim]—[/dim]",
        )

    console.print(f"\n  [green]☀[/green] [bold]7-Day Fasting Schedule[/bold]\n")
    console.print(table)
