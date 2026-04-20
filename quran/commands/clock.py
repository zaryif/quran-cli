"""
quran clock — live prayer clock with seconds and 5-waqt Namaz times.

Usage:
  quran clock        # live clock + prayer times (Ctrl+C to exit)
"""
from __future__ import annotations
import time
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
import typer

app     = typer.Typer(help="Live prayer clock with 5-waqt Namaz times.")
console = Console()

WAQT = [
    ("Fajr",    "الفجر",   "Dawn"),
    ("Dhuhr",   "الظهر",   "Midday"),
    ("Asr",     "العصر",   "Afternoon"),
    ("Maghrib", "المغرب",  "Sunset"),
    ("Isha",    "العشاء",  "Night"),
]


def _get_prayer_data():
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
    hijri_months = [
        "Muharram", "Safar", "Rabi Al-Awwal", "Rabi Al-Thani",
        "Jumada Al-Awwal", "Jumada Al-Thani", "Rajab", "Sha'aban",
        "Ramadan", "Shawwal", "Dhul-Qi'dah", "Dhul-Hijjah",
    ]
    hijri_str = f"{hd} {hijri_months[hm - 1]} {hy} AH"
    return pt, loc, hijri_str, is_ramadan(), cfg


def _fmt_countdown(next_dt: datetime, now: datetime) -> str:
    diff  = next_dt.replace(tzinfo=None) - now.replace(tzinfo=None)
    total = max(0, int(diff.total_seconds()))
    h, r  = divmod(total, 3600)
    m, s  = divmod(r, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _build_display(pt, loc: dict, hijri_str: str, is_ram: bool, cfg: dict):
    from quran.core.prayer_times import sehri_time, iftar_time

    now             = datetime.now()
    times           = pt.as_dict()
    next_name, next_dt = pt.next_prayer(now)
    cd              = _fmt_countdown(next_dt, now)
    city            = loc.get("city", "Unknown")
    country         = loc.get("country", "")
    method          = cfg.get("method", "Karachi")

    # ── Clock panel ────────────────────────────────────────────────
    clock_body = Text(justify="center")
    clock_body.append(now.strftime("%H:%M:%S"), style="bold green")
    clock_body.append(f"\n{now.strftime('%A, %d %B %Y')}", style="white")
    clock_body.append(f"\n{hijri_str}", style="dim white")
    clock_body.append(f"\n\n{city}, {country}", style="dim")
    if is_ram:
        clock_body.append("  ·  ☽ Ramadan Mubarak", style="yellow")

    clock_panel = Panel(
        Align.center(clock_body),
        title="[bold green]Prayer Clock[/bold green]",
        border_style="green",
        padding=(1, 8),
    )

    # ── Prayer times table ─────────────────────────────────────────
    tbl = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold dim",
        border_style="bright_black",
        padding=(0, 2),
        expand=True,
    )
    tbl.add_column("Waqt",   width=10)
    tbl.add_column("Arabic", width=10, justify="right")
    tbl.add_column("Time",   width=12)
    tbl.add_column("Status", width=24)

    for pname, par, _ in WAQT:
        dt = times.get(pname)
        if dt is None:
            continue
        t_str   = dt.strftime("%I:%M %p")
        is_next = pname == next_name
        is_done = dt.replace(tzinfo=None) < now.replace(tzinfo=None)

        if is_next:
            tbl.add_row(
                f"[bold green]{pname}[/bold green]",
                f"[bold yellow]{par}[/bold yellow]",
                f"[bold green]{t_str}[/bold green]",
                f"[green]▶  in {cd}[/green]",
            )
        elif is_done:
            tbl.add_row(
                f"[dim]{pname}[/dim]",
                f"[dim]{par}[/dim]",
                f"[dim]{t_str}[/dim]",
                "[dim]✓  done[/dim]",
            )
        else:
            tbl.add_row(pname, par, t_str, "[dim]—[/dim]")

    if is_ram:
        tbl.add_section()
        sh  = sehri_time(pt).strftime("%I:%M %p")
        ift = iftar_time(pt).strftime("%I:%M %p")
        tbl.add_row(
            "[yellow]Sehri[/yellow]",
            "[yellow]السحور[/yellow]",
            f"[yellow]{sh}[/yellow]",
            "[dim yellow]Ramadan[/dim yellow]",
        )
        tbl.add_row(
            "[yellow]Iftar[/yellow]",
            "[yellow]الإفطار[/yellow]",
            f"[yellow]{ift}[/yellow]",
            "[dim yellow]Ramadan[/dim yellow]",
        )

    prayer_panel = Panel(
        tbl,
        title="[dim]5 Waqt Namaz  ·  الصلوات الخمس[/dim]",
        border_style="bright_black",
        padding=(0, 1),
    )

    footer = Align.center(Text(
        f"Method: {method}  ·  Ctrl+C to exit",
        style="dim",
    ))

    outer = Table.grid(expand=True)
    outer.add_column()
    outer.add_row(clock_panel)
    outer.add_row(prayer_panel)
    outer.add_row(footer)
    return outer


@app.callback(invoke_without_command=True)
def clock_cmd(ctx: typer.Context):
    """Live prayer clock with 5-waqt Namaz times and countdown."""
    if ctx.invoked_subcommand:
        return
    _run_clock()


def _run_clock():
    console.print()
    with console.status("[dim]Loading prayer times…[/dim]"):
        try:
            pt, loc, hijri_str, is_ram, cfg = _get_prayer_data()
        except Exception as e:
            console.print(f"  [red]Error loading prayer times:[/red] {e}")
            return

    try:
        last_date = datetime.now().date()
        try:
            live_ctx = Live(console=console, refresh_per_second=1, screen=True)
        except Exception:
            # Fallback for terminals that don't support alternate screen
            live_ctx = Live(console=console, refresh_per_second=1, screen=False)
        with live_ctx as live:
            while True:
                now = datetime.now()
                if now.date() != last_date:
                    pt, loc, hijri_str, is_ram, cfg = _get_prayer_data()
                    last_date = now.date()
                live.update(_build_display(pt, loc, hijri_str, is_ram, cfg))
                time.sleep(1)
    except KeyboardInterrupt:
        pass
