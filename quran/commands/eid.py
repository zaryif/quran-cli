"""
quran eid — complete Eid guide with salah steps, timings, Qurbani.

Usage:
  quran eid              # next Eid overview
  quran eid fitr         # Eid ul-Fitr salah guide
  quran eid adha         # Eid ul-Adha + Qurbani guide
  quran eid --takbeer    # Takbeer text
"""
from __future__ import annotations
from datetime import date
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box
from typing_extensions import Annotated

app     = typer.Typer(help="Eid salah guide and details.")
console = Console()


EID_FITR_STEPS = [
    ("01", "Make intention (Niyyah)",
     "Niyyah for 2 rak'ahs Eid ul-Fitr Salah behind the Imam."),
    ("02", "Takbeer-e-Tahreema",
     "Allahu Akbar — fold hands. Imam raises hands, congregation follows."),
    ("03", "3 extra Takbeers in 1st rak'ah",
     "Say Allahu Akbar 3 times. Drop hands to sides between each. After 3rd, fold."),
    ("04", "Recite Al-Fatiha + another Surah",
     "Imam recites aloud. Recommended: Surah Al-A'la (87)."),
    ("05", "Complete 1st rak'ah normally",
     "Ruku → Sujood → sit → Sujood. Stand for 2nd rak'ah."),
    ("06", "3 extra Takbeers in 2nd rak'ah",
     "Before Al-Fatiha. After 3rd Takbeer, fold hands."),
    ("07", "Recite Al-Fatiha + Surah",
     "Recommended: Surah Al-Ghashiyah (88)."),
    ("08", "Complete 2nd rak'ah",
     "Ruku → Sujood → Tashahhud → Salaam (right, then left)."),
    ("09", "Listen to the Khutbah",
     "Obligatory to stay. Eid Khutbah comes AFTER salah — unlike Jumu'ah."),
]

EID_ADHA_STEPS = [
    ("01", "Ghusl before Salah", "Full bath is Sunnah before Eid prayer."),
    ("02", "Do NOT eat before Salah",
     "Unlike Eid ul-Fitr, delay eating until after prayer — ideally from Qurbani meat."),
    ("03", "Wear best clothes, apply itr",
     "Alcohol-free perfume only. Best garments you own."),
    ("04", "Takbeer aloud to Eidgah",
     "Allahu Akbar from Fajr 9th Dhul Hijjah to Asr 13th Dhul Hijjah."),
    ("05", "Perform Salah",
     "Same as Eid ul-Fitr: 2 rak'ahs, extra Takbeers in each rak'ah."),
    ("06", "Qurbani after Salah",
     "Slaughter begins after salah. Window: 10th–12th Dhul Hijjah. "
     "Say: Bismillahi Allahu Akbar, then face animal toward Qiblah."),
    ("07", "Distribute meat in thirds",
     "1/3 for yourself · 1/3 for relatives/friends · 1/3 for the poor."),
]

TAKBEER = {
    "arabic": "ٱللَّٰهُ أَكْبَرُ ٱللَّٰهُ أَكْبَرُ لَا إِلَٰهَ إِلَّا ٱللَّٰهُ وَٱللَّٰهُ أَكْبَرُ ٱللَّٰهُ أَكْبَرُ وَلِلَّٰهِ ٱلْحَمْدُ",
    "transliteration": (
        "Allahu Akbar, Allahu Akbar,\n"
        "La ilaha illallah,\n"
        "Allahu Akbar, Allahu Akbar,\n"
        "Wa lillahil hamd."
    ),
    "meaning": "Allah is the Greatest, Allah is the Greatest. There is no god but Allah. Allah is the Greatest, Allah is the Greatest. All praise be to Allah.",
}

# Approximate Gregorian Eid dates
EID_DATES = {
    "fitr": {
        1447: date(2026, 3, 20),
        1448: date(2027, 3, 10),
    },
    "adha": {
        1447: date(2026, 5, 27),
        1448: date(2027, 5, 17),
    },
}


def _current_hijri_year() -> int:
    from quran.core.ramadan import gregorian_to_hijri
    hy, _, _ = gregorian_to_hijri(date.today())
    return hy


@app.callback(invoke_without_command=True)
def eid_cmd(
    ctx:     typer.Context,
    takbeer: Annotated[bool, typer.Option("--takbeer", help="Show Eid Takbeer text")] = False,
):
    if ctx.invoked_subcommand:
        return
    if takbeer:
        _show_takbeer()
        return
    _show_overview()


@app.command("fitr")
def eid_fitr():
    """Eid ul-Fitr salah guide."""
    from quran.core.location import detect_location
    from quran.config.settings import load

    cfg = load()
    loc = detect_location()
    hy  = _current_hijri_year()

    eid_date = EID_DATES["fitr"].get(hy, EID_DATES["fitr"].get(hy+1))

    console.print()
    console.print(Rule("[bold]☽ Eid ul-Fitr[/bold]", style="green"))
    console.print()

    if eid_date:
        console.print(f"  [dim]Expected:[/dim] [bold white]{eid_date.strftime('%d %B %Y')}[/bold white]  "
                      f"[dim](subject to moon sighting)[/dim]")
    console.print(f"  [dim]Location:[/dim] {loc.get('city','?')}, {loc.get('country','?')}")
    console.print(f"  [dim]Salah time:[/dim] [bold]~07:15 AM[/bold]  [dim](confirm locally)[/dim]")
    console.print()

    # Sunnah acts before
    console.print("  [dim]Sunnah before Salah:[/dim]")
    for act in ["Ghusl (full bath)", "Eat dates (odd number) before going",
                "Wear best clothes", "Go one route, return another",
                "Recite Takbeer quietly on way to Eidgah"]:
        console.print(f"  [green]·[/green] {act}")
    console.print()

    # Salah steps
    console.print("  [bold]Salah — step by step[/bold]")
    console.print()
    _print_steps(EID_FITR_STEPS)

    # Zakat ul-Fitr
    console.print(Rule("[dim]Zakat ul-Fitr[/dim]", style="bright_black"))
    console.print("  Must be paid [bold]before[/bold] Eid salah.")
    console.print("  Amount: [bold]~2.5 kg[/bold] of staple food or its cash equivalent per person.")
    console.print()

    _show_takbeer()


@app.command("adha")
def eid_adha():
    """Eid ul-Adha guide and Qurbani details."""
    from quran.core.location import detect_location
    from quran.config.settings import load

    cfg = load()
    loc = detect_location()
    hy  = _current_hijri_year()

    eid_date = EID_DATES["adha"].get(hy, EID_DATES["adha"].get(hy+1))

    console.print()
    console.print(Rule("[bold]✦ Eid ul-Adha[/bold]", style="yellow"))
    console.print()

    if eid_date:
        console.print(f"  [dim]Expected:[/dim] [bold white]{eid_date.strftime('%d %B %Y')}[/bold white]  "
                      f"[dim](subject to moon sighting)[/dim]")
    console.print(f"  [dim]Qurbani window:[/dim] [bold]10th – 12th Dhul Hijjah[/bold] (3 days)")
    console.print()

    console.print("  [bold]Sunnah acts & guide[/bold]")
    console.print()
    _print_steps(EID_ADHA_STEPS)

    # Qurbani animals table
    console.print(Rule("[dim]Qurbani animals[/dim]", style="bright_black"))
    table = Table(box=box.SIMPLE, show_header=True, header_style="dim",
                  border_style="bright_black", padding=(0,2))
    table.add_column("Animal",    width=16)
    table.add_column("Age (min)", width=12, style="dim")
    table.add_column("Shares",    width=10)
    table.add_column("Note",      width=24, style="dim")

    table.add_row("Goat / Sheep", "1 year",  "1 person",   "Fully covers 1 household")
    table.add_row("Cow / Buffalo","2 years", "up to 7",    "7 people can share")
    table.add_row("Camel",        "5 years", "up to 7",    "Most reward per animal")
    console.print(table)

    console.print()
    console.print("  [dim]Meat distribution:[/dim]")
    console.print("  [yellow]1/3[/yellow] for yourself & family")
    console.print("  [yellow]1/3[/yellow] for relatives & friends")
    console.print("  [yellow]1/3[/yellow] for the poor")
    console.print()

    _show_takbeer()


def _show_overview() -> None:
    hy   = _current_hijri_year()
    today = date.today()

    console.print()
    console.print(Rule("[bold]✦ Eid Guide[/bold]", style="green"))
    console.print()

    for eid_type, label, color in [("fitr", "Eid ul-Fitr", "green"), ("adha", "Eid ul-Adha", "yellow")]:
        eid_date = EID_DATES[eid_type].get(hy) or EID_DATES[eid_type].get(hy+1)
        if eid_date:
            days = (eid_date - today).days
            if days > 0:
                countdown = f"[dim]in {days} days[/dim]"
            elif days == 0:
                countdown = f"[bold {color}]TODAY[/bold {color}]"
            else:
                countdown = f"[dim]passed[/dim]"
            console.print(f"  [{color}]{label}[/{color}]  "
                          f"[white]{eid_date.strftime('%d %B %Y')}[/white]  {countdown}")

    console.print()
    console.print("  [dim]quran eid fitr   [/dim][green]→[/green] [dim]Eid ul-Fitr salah guide[/dim]")
    console.print("  [dim]quran eid adha   [/dim][green]→[/green] [dim]Eid ul-Adha + Qurbani[/dim]")
    console.print("  [dim]quran eid --takbeer[/dim] [green]→[/green] [dim]Takbeer text[/dim]")
    console.print()


def _show_takbeer() -> None:
    console.print()
    console.print(Rule("[dim]Eid Takbeer[/dim]", style="bright_black"))
    console.print()
    console.print(f"  [yellow]{TAKBEER['arabic']}[/yellow]")
    console.print()
    console.print(f"  [dim]{TAKBEER['transliteration']}[/dim]")
    console.print()
    console.print(f"  [dim]Meaning: {TAKBEER['meaning']}[/dim]")
    console.print()


def _print_steps(steps: list) -> None:
    for num, title, detail in steps:
        console.print(f"  [green]{num}[/green]  [white]{title}[/white]")
        if detail:
            console.print(f"      [dim]{detail}[/dim]")
    console.print()
