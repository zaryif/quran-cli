"""
quran namaz — detailed guide for performing each prayer.

Usage:
  quran namaz                # interactive picker
  quran namaz fajr           # Fajr guide
  quran namaz jummah         # Jumu'ah guide
  quran namaz tarawih        # Tarawih guide
  quran namaz witr           # Witr guide
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.text import Text
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Detailed Salah performance guide.")
console = Console()

PRAYERS = {
    "fajr": {
        "name": "Fajr",  "arabic": "صَلَاة الفَجر",  "time_desc": "Dawn to sunrise",
        "sunnah_before": 2,  "fard": 2,  "sunnah_after": 0,  "nafl": 0,
        "significance": (
            "The dawn prayer — among the most virtuous of all prayers. "
            "Whoever prays Fajr is under the protection of Allah for that day. "
            "The Prophet (ﷺ) said: 'The two rak'ahs of Fajr are better than this world and all it contains.' (Muslim)"
        ),
        "common_mistakes": [
            "Praying after sunrise — Fajr must be completed before the sun fully rises",
            "Rushing the 2 Sunnah rak'ahs before Fard",
            "Missing Fajr due to sleep — set an alarm or reminder",
        ],
        "duaa": "Allahumma inni as'aluka 'ilman naafi'an wa rizqan tayyiban...",
    },
    "dhuhr": {
        "name": "Dhuhr", "arabic": "صَلَاة الظُّهر", "time_desc": "Sun passes zenith to Asr",
        "sunnah_before": 4, "fard": 4, "sunnah_after": 2, "nafl": 2,
        "significance": (
            "The midday prayer. The Prophet (ﷺ) said the gates of heaven open at midday "
            "and he loved that a good deed be raised at that time. A time of rest and reflection "
            "at the height of the working day."
        ),
        "common_mistakes": [
            "Shortening the Sunnah rak'ahs when at home",
            "Missing Dhuhr because of work — combine intentions with lunch break",
        ],
        "duaa": "SubhanAllahi wa bihamdihi, SubhanAllahil 'Azeem",
    },
    "asr": {
        "name": "Asr",  "arabic": "صَلَاة العَصر", "time_desc": "Afternoon to sunset",
        "sunnah_before": 4, "fard": 4, "sunnah_after": 0, "nafl": 0,
        "significance": (
            "The 'middle prayer' (Al-Salat Al-Wusta). Allah takes special care to mention it in "
            "the Quran [2:238]. The Prophet (ﷺ) said: 'Whoever misses Asr, it is as if he has "
            "lost his family and wealth.' (Bukhari). Guard it carefully."
        ),
        "common_mistakes": [
            "Missing Asr due to late afternoon work or meetings",
            "Praying after sunset (only permissible if genuinely missed with excuse)",
            "Forgetting the 4 Sunnah Ghair Muakkadah before Fard",
        ],
        "duaa": "Astaghfirullaha Rabbi min kulli dhambin wa atubu ilayh",
    },
    "maghrib": {
        "name": "Maghrib", "arabic": "صَلَاة المَغرب", "time_desc": "Sunset to ~1.5h after",
        "sunnah_before": 0, "fard": 3, "sunnah_after": 2, "nafl": 2,
        "significance": (
            "The sunset prayer — its window is brief (about 1.5 hours). "
            "The Quran was revealed to mention glorifying Allah at sunset. "
            "During Ramadan, Iftar is at Maghrib — break fast with dates and water, then pray."
        ),
        "common_mistakes": [
            "Delaying Maghrib without reason — its time is short",
            "Eating a full Iftar meal before praying in Ramadan (eat lightly first, pray, then eat)",
        ],
        "duaa": "Allahuma inni as'aluka bil-qudratil-qadima...",
    },
    "isha": {
        "name": "Isha",  "arabic": "صَلَاة العِشاء", "time_desc": "Night (after twilight) to midnight",
        "sunnah_before": 4, "fard": 4, "sunnah_after": 2, "nafl": 2,
        "witr": 3,
        "significance": (
            "The night prayer. The Prophet (ﷺ) said: 'Whoever prays Isha in congregation "
            "is as if he stood half the night in prayer.' (Muslim). "
            "Witr (3 rak'ahs) should be the last prayer before sleep."
        ),
        "common_mistakes": [
            "Sleeping before Isha without praying",
            "Forgetting Witr — it is Wajib (obligatory) according to the Hanafi madhab",
            "Praying Isha after midnight without necessity",
        ],
        "duaa": "Allahuma qini 'adhabaka yawma tab'athu 'ibadak",
    },
    "jummah": {
        "name": "Jumu'ah (Friday)", "arabic": "صَلَاة الجُمُعَة",
        "time_desc": "Replaces Dhuhr on Friday",
        "sunnah_before": 4, "fard": 2, "sunnah_after": 4, "nafl": 0,
        "significance": (
            "The best day of the week — the Day of Jumu'ah. "
            "The Prophet (ﷺ) said: 'Friday is the master of days.' (Ibn Majah). "
            "Attend khutbah and congregation. Recommended: ghusl, itr, early arrival, Surah Al-Kahf."
        ),
        "common_mistakes": [
            "Missing 3 consecutive Jumu'ah without excuse — a major sin",
            "Arriving late and missing the khutbah",
            "Not reciting Surah Al-Kahf on Friday",
        ],
        "duaa": "Allahumma salli 'ala Muhammadin wa 'ala ali Muhammad",
    },
    "tarawih": {
        "name": "Tarawih", "arabic": "صَلَاة التَّراوِيح",
        "time_desc": "After Isha during Ramadan",
        "sunnah_before": 0, "fard": 0, "sunnah_after": 0, "nafl": 20,
        "significance": (
            "The Ramadan night prayer — 20 rak'ahs (or 8, per some madhabs) after Isha. "
            "The Prophet (ﷺ) said: 'Whoever stands in prayer during Ramadan out of sincere faith "
            "and hoping for reward, his previous sins will be forgiven.' (Bukhari). "
            "Witr (3 rak'ahs) is prayed at the end of Tarawih."
        ),
        "common_mistakes": [
            "Rushing the prayer — Tarawih should be calm and reflective",
            "Missing last 10 nights — the most virtuous period",
            "Not making intention to seek Laylatul Qadr",
        ],
        "duaa": "SubhanAllah (33x), Alhamdulillah (33x), Allahu Akbar (34x) after each 2 rak'ahs",
    },
    "witr": {
        "name": "Witr", "arabic": "صَلَاة الوِتر",
        "time_desc": "After Isha, before Fajr (last prayer of night)",
        "sunnah_before": 0, "fard": 0, "sunnah_after": 0, "nafl": 3,
        "significance": (
            "Witr means 'odd number'. Wajib according to Hanafi; Sunnah Muakkadah for others. "
            "The Prophet (ﷺ) never missed Witr, even while travelling. "
            "In the 3rd rak'ah: recite Al-Fatiha + Al-A'la + Qunoot du'a before ruku."
        ),
        "common_mistakes": [
            "Skipping Witr entirely",
            "Not reciting Qunoot du'a in the third rak'ah",
            "Praying Witr before Isha",
        ],
        "duaa": "Allahuma ihdini fiman hadayt, wa 'afini fiman 'afayt... (full Qunoot)",
    },
}


@app.callback(invoke_without_command=True)
def namaz_cmd(
    ctx:   typer.Context,
    prayer: Annotated[Optional[str], typer.Argument(
        help="fajr, dhuhr, asr, maghrib, isha, jummah, tarawih, witr")] = None,
):
    if ctx.invoked_subcommand:
        return

    if not prayer:
        _interactive_picker()
        return

    key = prayer.lower()
    if key not in PRAYERS:
        console.print(f"[red]✗[/red] Unknown prayer: {prayer}")
        console.print(f"[dim]Options: {', '.join(PRAYERS.keys())}[/dim]")
        return

    _show_prayer(PRAYERS[key])


def _interactive_picker():
    console.print()
    console.print(Rule("[dim]Prayer Details (Rakat)[/dim]", style="green"))
    console.print()

    keys = list(PRAYERS.keys())

    try:
        from simple_term_menu import TerminalMenu

        labels = []
        for k in keys:
            p = PRAYERS[k]
            labels.append(f"{p['name']:10s}  {p['arabic']}   {p['time_desc']}")

        console.print("  [dim]↑↓ to navigate · Enter to select · q to cancel[/dim]\n")

        menu = TerminalMenu(
            labels,
            title="  Select a prayer:",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green", "bold"),
        )
        idx = menu.show()

        if idx is not None:
            _show_prayer(PRAYERS[keys[idx]])
        else:
            console.print("  [dim]Cancelled.[/dim]")

    except ImportError:
        # Fallback: numbered list
        console.print("  [dim]Select a prayer:[/dim]")
        for i, k in enumerate(keys, 1):
            p = PRAYERS[k]
            console.print(f"  [green]{i}[/green]  {p['name']}  [dim]{p['arabic']}[/dim]")
        console.print()
        console.print("[dim]Enter number:[/dim] ", end="")
        try:
            idx = int(input().strip()) - 1
            _show_prayer(PRAYERS[keys[idx]])
        except (ValueError, IndexError):
            console.print("[dim]Cancelled.[/dim]")


def _show_prayer(p: dict):
    console.print()
    console.print(Rule(
        f"[bold green]{p['name']}[/bold green]  [yellow]{p['arabic']}[/yellow]",
        style="bright_black"
    ))
    console.print()

    # Time info
    from quran.core.prayer_times import get_prayer_times
    from quran.core.location import detect_location
    from quran.config.settings import load

    try:
        cfg = load()
        loc = detect_location()
        pt  = get_prayer_times(loc["lat"], loc["lon"],
                               method=cfg.get("method","Karachi"),
                               tz=loc.get("tz",""))
        time_map = {
            "fajr": pt.fajr, "dhuhr": pt.dhuhr, "asr": pt.asr,
            "maghrib": pt.maghrib, "isha": pt.isha,
        }
        key = p["name"].lower().split()[0]
        if key in time_map:
            t = time_map[key]
            console.print(f"  [dim]Today:[/dim] [bold green]{t.strftime('%I:%M %p')}[/bold green]  "
                          f"[dim]{p['time_desc']}[/dim]")
            console.print()
    except Exception:
        console.print(f"  [dim]{p['time_desc']}[/dim]\n")

    # Rakah breakdown
    _print_rakah_breakdown(p)

    # Significance
    console.print(f"  [dim]{p['significance']}[/dim]")
    console.print()

    # Common mistakes
    if p.get("common_mistakes"):
        console.print("  [bold]Common mistakes:[/bold]")
        for m in p["common_mistakes"]:
            console.print(f"  [red]·[/red] [dim]{m}[/dim]")
        console.print()

    # Du'a
    if p.get("duaa"):
        console.print(f"  [dim]Du'a after salah:[/dim]")
        console.print(f"  [dim]{p['duaa']}[/dim]")
        console.print()

    console.print(f"  [dim]AI guide: [green]quran guide \"how to perform {p['name'].lower()}\"[/green][/dim]\n")


def _print_rakah_breakdown(p: dict):
    rows = []
    if p.get("sunnah_before", 0):
        rows.append(("Sunnah before", p["sunnah_before"], "dim"))
    if p.get("fard", 0):
        rows.append(("Fard (obligatory)", p["fard"], "bold green"))
    if p.get("sunnah_after", 0):
        rows.append(("Sunnah after", p["sunnah_after"], "dim"))
    if p.get("nafl", 0):
        rows.append(("Nafl", p["nafl"], "dim"))
    if p.get("witr", 0):
        rows.append(("Witr", p["witr"], "yellow"))

    if not rows:
        return

    total = sum(r[1] for r in rows if r[2] != "dim")

    table = Table(box=box.SIMPLE, show_header=False, padding=(0,2), border_style="bright_black")
    table.add_column("Type",   width=20)
    table.add_column("Rak'ah", width=8)
    table.add_column("Dots",   width=20)

    for label, count, style in rows:
        dots = ""
        if style == "bold green":
            dots = "[green]" + "● " * count + "[/green]"
        elif style == "yellow":
            dots = "[yellow]" + "● " * count + "[/yellow]"
        else:
            dots = "[dim]○ " * count + "[/dim]"
        table.add_row(f"[{style}]{label}[/{style}]", f"[{style}]{count}[/{style}]", dots)

    console.print(table)
    console.print()
