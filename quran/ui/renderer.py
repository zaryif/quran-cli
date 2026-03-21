"""
quran-cli terminal renderer — Rich-powered professional UI.
Clean Arabic display, minimal aesthetic, professional splash.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.align import Align
from rich import box

console = Console()

GREEN  = "green"
AMBER  = "yellow"
DIM    = "dim"
WHITE  = "white bold"
MUTED  = "bright_black"

# ── Arabic text constants ──────────────────────────────────────────────────────
# All strings are correct pre-composed Unicode Arabic.
# They display correctly in any Unicode-capable terminal.
BASMALLAH    = "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ"
AL_QURAN     = "ٱلۡقُرۡءَانُ ٱلۡكَرِيمُ"
AL_FATIHA_1  = "ٱلۡحَمۡدُ لِلَّهِ رَبِّ ٱلۡعَٰلَمِينَ"
AL_FATIHA_2  = "ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ"
AYAT_KURSI_AR= "ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ ٱلۡحَيُّ ٱلۡقَيُّومُ"


def _shape(text: str) -> str:
    """
    Correctly shape and display Arabic text in terminal.
    Uses arabic-reshaper + python-bidi for proper glyph joining and RTL.
    Falls back to raw Unicode (still renders correctly in most modern terminals).
    """
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


def print_banner() -> None:
    """
    Professional quran-cli splash screen.
    Basmallah displayed clearly in Arabic, clean command hints.
    """
    from quran.core.ramadan import is_ramadan

    c = console
    ram = is_ramadan()

    # Shape Arabic text for the terminal
    basmallah_s = _shape(BASMALLAH)
    al_quran_s  = _shape(AL_QURAN)

    # Top spacer
    c.print()

    # ── Basmallah block ────────────────────────────────────────────────────────
    # Displayed separately above panel for maximum readability
    c.print(Align.center(Text(basmallah_s, style="bold yellow")))
    c.print(Align.center(
        Text("In the name of Allah, the Most Gracious, the Most Merciful",
             style="dim italic")
    ))
    c.print()

    # ── App identity ───────────────────────────────────────────────────────────
    c.print(Align.center(Text("quran-cli", style="bold green")))
    c.print(Align.center(Text(f"v1.0.0  ·  Islamic terminal companion", style="dim")))

    if ram:
        c.print()
        c.print(Align.center(Text("☽  Ramadan Mubarak", style="bold yellow")))

    c.print()

    # ── Quick-start panel ──────────────────────────────────────────────────────
    commands = [
        ("quran schedule",          "full day view — prayers, sehri, iftar"),
        ("quran read 1",            "read Al-Fatihah"),
        ("quran read kahf",         "search surah by name"),
        ("quran read 2:255 --dual", "Ayat ul-Kursi with Arabic"),
        ("quran pray",              "today's prayer times"),
        ("quran ramadan",           "sehri, iftar & tarawih"),
        ("quran guide \"...\"",     "ask the Quran & Hadith AI guide"),
        ("quran --help",            "all commands"),
    ]

    rows = "\n".join(
        f"  [green]{cmd:<35}[/green][dim]{desc}[/dim]"
        for cmd, desc in commands
    )

    c.print(Panel(
        rows,
        title=f"[dim]quick start[/dim]",
        border_style="bright_black",
        padding=(0, 1),
    ))
    c.print()


def print_location_header(loc: dict, is_ramadan: bool = False) -> None:
    """Print location + Ramadan mode indicator."""
    city    = loc.get("city", "?")
    country = loc.get("country", "?")
    lat     = loc.get("lat", 0)
    lon     = loc.get("lon", 0)
    auto    = loc.get("auto", False)

    tag = "[green][auto][/green]" if auto else "[dim][manual][/dim]"
    ram = "  [yellow]☽ Ramadan[/yellow]" if is_ramadan else ""

    console.print(
        f" [green]◉[/green]  [bold]{city}, {country}[/bold]  {tag}  "
        f"[dim]{lat:.4f}°N · {lon:.4f}°E[/dim]{ram}"
    )
    console.print()


def print_ayah_arabic(text: str) -> None:
    """Print Arabic ayah text, right-aligned, properly shaped."""
    shaped = _shape(text)
    console.print(Align.right(
        Text(shaped, style="bold yellow", justify="right"),
        width=min(console.width - 4, 80)
    ))


def render_prayer_table(
    times: dict,
    next_name: Optional[str] = None,
    extras: Optional[dict] = None,
) -> None:
    """Render prayer times as a clean table."""
    table = Table(
        box=box.SIMPLE, show_header=False,
        padding=(0, 2), border_style="bright_black",
    )
    table.add_column("Prayer", style="dim",   width=12)
    table.add_column("Time",   style="white", width=12)
    table.add_column("",                      width=16)

    order = []
    if extras and "Sehri" in extras:
        order.append(("Sehri", True))
    order += [("Fajr", False), ("Sunrise", False), ("Dhuhr", False), ("Asr", False)]
    if extras and "Iftar" in extras:
        order.append(("Iftar", True))
    order += [("Maghrib", False), ("Isha", False)]
    if extras and "Tarawih" in extras:
        order.append(("Tarawih", True))

    all_times = dict(times)
    if extras:
        all_times.update(extras)

    ARABIC_NAMES = {
        "Fajr": "فَجْر", "Sunrise": "شُرُوق",
        "Dhuhr": "ظُهْر", "Asr": "عَصْر",
        "Maghrib": "مَغْرِب", "Isha": "عِشَاء",
        "Sehri": "سُحُور", "Iftar": "إِفْطَار", "Tarawih": "تَرَاوِيح",
    }

    for name, is_special in order:
        dt = all_times.get(name)
        if not isinstance(dt, __import__("datetime").datetime):
            continue
        time_str  = dt.strftime("%I:%M %p")
        ar_name   = _shape(ARABIC_NAMES.get(name, ""))
        is_next   = name == next_name

        if is_next:
            table.add_row(
                f"[bold green]{name}[/bold green]",
                f"[bold green]{time_str}[/bold green]",
                f"[green]▶ next[/green]  [dim]{ar_name}[/dim]",
            )
        elif is_special:
            table.add_row(
                f"[yellow]{name}[/yellow]",
                f"[yellow]{time_str}[/yellow]",
                f"[dim yellow]{ar_name}[/dim yellow]",
            )
        elif name == "Sunrise":
            table.add_row(
                f"[dim]{name}[/dim]",
                f"[dim]{time_str}[/dim]",
                f"[dim]{ar_name}[/dim]",
            )
        else:
            table.add_row(name, time_str, f"[dim]{ar_name}[/dim]")

    console.print(table)


def render_surah_header(meta: dict) -> None:
    """Surah section header with name, meaning, type."""
    console.print()
    console.print(Rule(
        f"[bold green]{meta['name']}[/bold green]  "
        f"[dim]{meta['meaning']}  ·  {meta['ayahs']} ayahs  ·  {meta['type']}[/dim]",
        style="green"
    ))
    console.print()


def render_schedule_table(rows: list[dict]) -> None:
    """Full-day schedule with progress bars."""
    table = Table(
        box=box.SIMPLE_HEAD, show_header=True,
        header_style="dim", border_style="bright_black",
        padding=(0, 1),
    )
    table.add_column("Prayer",   width=10)
    table.add_column("Time",     width=12, style="white")
    table.add_column("Progress", width=22)
    table.add_column("Status",   width=10)

    now = datetime.now()

    for row in rows:
        dt      = row["dt"]
        name    = row["name"]
        status  = row.get("status", "open")
        special = row.get("special", False)
        pct     = row.get("pct", 0)

        bar_w  = 18
        filled = int(bar_w * pct / 100)
        empty  = bar_w - filled

        if status == "next":
            bar    = f"[green]{'█' * filled}{'░' * empty}[/green]"
            name_s = f"[bold green]{name}[/bold green]"
            time_s = f"[bold green]{dt.strftime('%I:%M %p')}[/bold green]"
            stat_s = "[green]▶ next[/green]"
        elif status == "done":
            bar    = f"[bright_black]{'█' * filled}{'░' * empty}[/bright_black]"
            name_s = f"[dim]{name}[/dim]"
            time_s = f"[dim]{dt.strftime('%I:%M %p')}[/dim]"
            stat_s = "[dim]✓[/dim]"
        elif special:
            bar    = f"[yellow]{'█' * filled}{'░' * empty}[/yellow]"
            name_s = f"[yellow]{name}[/yellow]"
            time_s = f"[yellow]{dt.strftime('%I:%M %p')}[/yellow]"
            stat_s = "[dim yellow]—[/dim yellow]"
        else:
            bar    = f"[bright_black]{'░' * bar_w}[/bright_black]"
            name_s = name
            time_s = dt.strftime("%I:%M %p")
            stat_s = "[dim]—[/dim]"

        table.add_row(name_s, time_s, bar, stat_s)

    console.print(table)


def countdown_str(dt: datetime) -> str:
    """Human-readable countdown: '1h 23m' or '14m 07s'."""
    delta = dt - datetime.now()
    total = int(delta.total_seconds())
    if total <= 0:
        return "now"
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"
