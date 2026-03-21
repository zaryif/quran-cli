"""
quran lang — interactive language customisation.

Sets which language(s) appear in:
  - The splash screen (Arabic + English + your chosen language)
  - quran read (primary translation)
  - quran guide, quran quote, tafsir

Usage:
  quran lang              # interactive picker
  quran lang bn           # set primary to Bangla
  quran lang --second ur  # set secondary (splash) language
  quran lang --list       # show all available languages
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Set display language for translations.")
console = Console()

# Full language registry with native names + Basmallah translation preview
LANGUAGES = {
    "en": {
        "name":      "English",
        "native":    "English",
        "basmallah": "In the name of Allah, the Most Gracious, the Most Merciful",
        "edition":   "en.sahih",
        "translator":"Sahih International",
    },
    "bn": {
        "name":      "Bangla",
        "native":    "বাংলা",
        "basmallah": "আল্লাহর নামে, যিনি পরম দয়ালু, অতি মেহেরবান",
        "edition":   "bn.bengali",
        "translator":"Bengali Translation",
    },
    "ar": {
        "name":      "Arabic",
        "native":    "العربية",
        "basmallah": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ",
        "edition":   "ar.alafasy",
        "translator":"Arabic (Mushaf)",
    },
    "ur": {
        "name":      "Urdu",
        "native":    "اردو",
        "basmallah": "اللہ کے نام سے جو بڑا مہربان، نہایت رحم والا ہے",
        "edition":   "ur.jalandhry",
        "translator":"Jalandhry",
    },
    "tr": {
        "name":      "Turkish",
        "native":    "Türkçe",
        "basmallah": "Rahman ve Rahim olan Allah'ın adıyla",
        "edition":   "tr.diyanet",
        "translator":"Diyanet İşleri",
    },
    "fr": {
        "name":      "French",
        "native":    "Français",
        "basmallah": "Au nom d'Allah, le Tout Miséricordieux, le Très Miséricordieux",
        "edition":   "fr.hamidullah",
        "translator":"Hamidullah",
    },
    "id": {
        "name":      "Indonesian",
        "native":    "Bahasa Indonesia",
        "basmallah": "Dengan nama Allah Yang Maha Pengasih, Maha Penyayang",
        "edition":   "id.indonesian",
        "translator":"Kementerian Agama",
    },
    "ru": {
        "name":      "Russian",
        "native":    "Русский",
        "basmallah": "Во имя Аллаха, Милостивого, Милосердного",
        "edition":   "ru.kuliev",
        "translator":"Kuliev",
    },
    "de": {
        "name":      "German",
        "native":    "Deutsch",
        "basmallah": "Im Namen Allahs, des Allerbarmers, des Barmherzigen",
        "edition":   "de.bubenheim",
        "translator":"Bubenheim",
    },
    "es": {
        "name":      "Spanish",
        "native":    "Español",
        "basmallah": "En el nombre de Allah, el Compasivo, el Misericordioso",
        "edition":   "es.cortes",
        "translator":"Cortes",
    },
    "zh": {
        "name":      "Chinese",
        "native":    "中文",
        "basmallah": "奉至仁至慈的真主之名",
        "edition":   "zh.jian",
        "translator":"Jian",
    },
    "nl": {
        "name":      "Dutch",
        "native":    "Nederlands",
        "basmallah": "In de naam van Allah, de Erbarmer, de Genadevolle",
        "edition":   "nl.keyzer",
        "translator":"Keyzer",
    },
    "ms": {
        "name":      "Malay",
        "native":    "Bahasa Melayu",
        "basmallah": "Dengan nama Allah Yang Maha Pemurah lagi Maha Penyayang",
        "edition":   "ms.basmeih",
        "translator":"Basmeih",
    },
}


@app.callback(invoke_without_command=True)
def lang_cmd(
    ctx:    typer.Context,
    code:   Annotated[Optional[str], typer.Argument(
        help="Language code: en, bn, ar, ur, tr, fr, id, ru, de, es, zh, nl, ms"
    )] = None,
    second: Annotated[Optional[str], typer.Option(
        "--second", "-2",
        help="Set secondary (splash screen) language"
    )] = None,
    list_:  Annotated[bool, typer.Option(
        "--list", "-l",
        help="List all available languages"
    )] = False,
    reset:  Annotated[bool, typer.Option(
        "--reset",
        help="Reset to default (primary: en, secondary: bn)"
    )] = False,
):
    """Interactive language customisation for Quran reading and splash screen."""
    if ctx.invoked_subcommand:
        return

    from quran.config.settings import load, save

    if reset:
        cfg = load()
        cfg["lang"]  = "en"
        cfg["lang2"] = "bn"
        cfg["display"]["show_en"]    = True
        cfg["display"]["show_lang2"] = True
        save(cfg)
        console.print("[green]✓[/green] Reset: primary [bold]en[/bold] · secondary [bold]bn[/bold]")
        _show_preview("en", "bn")
        return

    if list_:
        _show_language_table()
        return

    # Direct set via arg
    if code:
        code = code.lower().strip()
        if code not in LANGUAGES:
            console.print(f"[red]✗[/red] Unknown code: [bold]{code}[/bold]")
            _show_language_table()
            return
        cfg = load()
        cfg["lang"] = code
        save(cfg)
        lang2 = cfg.get("lang2", "bn")
        console.print(f"[green]✓[/green] Primary language → [bold green]{LANGUAGES[code]['name']} ({LANGUAGES[code]['native']})[/bold green]")
        _show_preview(code, lang2)

        if second:
            second = second.lower().strip()
            if second in LANGUAGES:
                cfg = load()
                cfg["lang2"] = second
                save(cfg)
                console.print(f"[green]✓[/green] Secondary language → [bold cyan]{LANGUAGES[second]['name']} ({LANGUAGES[second]['native']})[/bold cyan]")
        return

    if second:
        second = second.lower().strip()
        if second not in LANGUAGES:
            console.print(f"[red]✗[/red] Unknown code: [bold]{second}[/bold]")
            _show_language_table()
            return
        cfg = load()
        cfg["lang2"] = second
        save(cfg)
        lang = cfg.get("lang", "en")
        console.print(f"[green]✓[/green] Secondary language → [bold cyan]{LANGUAGES[second]['name']} ({LANGUAGES[second]['native']})[/bold cyan]")
        _show_preview(lang, second)
        return

    # Interactive picker
    _interactive_picker()


def _interactive_picker() -> None:
    """Full interactive language selection."""
    from quran.config.settings import load, save

    cfg   = load()
    cur_p = cfg.get("lang", "en")
    cur_s = cfg.get("lang2", "bn")

    console.print()
    console.print(Rule("[dim]Language settings[/dim]", style="green"))
    console.print()
    console.print(f"  Current primary:   [bold green]{LANGUAGES.get(cur_p, {}).get('name', cur_p)}[/bold green] [dim]({cur_p})[/dim]")
    console.print(f"  Current secondary: [bold cyan]{LANGUAGES.get(cur_s, {}).get('name', cur_s)}[/bold cyan] [dim]({cur_s})[/dim]")
    console.print()

    _show_language_table(current_p=cur_p, current_s=cur_s)

    console.print()
    console.print("[dim]Primary language code (for reading & all commands):[/dim] ", end="")
    inp_p = input().strip().lower()
    if inp_p and inp_p in LANGUAGES:
        cfg["lang"] = inp_p
        console.print(f"  [green]✓[/green] Primary → [bold]{LANGUAGES[inp_p]['name']}[/bold]")
    elif inp_p:
        console.print(f"  [yellow]![/yellow] '{inp_p}' not recognised, keeping [bold]{cur_p}[/bold]")

    console.print("[dim]Secondary language (shown on splash screen):[/dim] ", end="")
    inp_s = input().strip().lower()
    if inp_s and inp_s in LANGUAGES:
        cfg["lang2"] = inp_s
        console.print(f"  [green]✓[/green] Secondary → [bold]{LANGUAGES[inp_s]['name']}[/bold]")
    elif inp_s:
        console.print(f"  [yellow]![/yellow] '{inp_s}' not recognised, keeping [bold]{cur_s}[/bold]")

    save(cfg)
    console.print()

    new_p = cfg.get("lang", cur_p)
    new_s = cfg.get("lang2", cur_s)
    _show_preview(new_p, new_s)


def _show_language_table(current_p: str = "", current_s: str = "") -> None:
    """Print all available languages as a table."""
    table = Table(
        box=box.SIMPLE_HEAD, show_header=True,
        header_style="dim", border_style="bright_black",
        padding=(0, 2),
    )
    table.add_column("Code",        width=6)
    table.add_column("Language",    width=14)
    table.add_column("Native",      width=16)
    table.add_column("Translator",  width=22, style="dim")
    table.add_column("",            width=6)

    for code, info in LANGUAGES.items():
        markers = ""
        if code == current_p:
            markers += "[green]P[/green]"
        if code == current_s:
            markers += "[cyan]S[/cyan]"
        table.add_row(
            f"[bold]{code}[/bold]",
            info["name"],
            info["native"],
            info["translator"],
            markers,
        )

    console.print(table)
    console.print("[dim]  P = current primary · S = current secondary[/dim]")


def _show_preview(lang_p: str, lang_s: str) -> None:
    """Show how the splash screen will look with these settings."""
    from quran.ui.renderer import _shape, BASMALLAH

    p_info = LANGUAGES.get(lang_p, {})
    s_info = LANGUAGES.get(lang_s, {})

    ar      = _shape(BASMALLAH)
    en_text = LANGUAGES["en"]["basmallah"]
    p_text  = p_info.get("basmallah", "")
    s_text  = s_info.get("basmallah", "")

    console.print()
    console.print(Panel(
        f"  [bold yellow]{ar}[/bold yellow]\n"
        f"  [white]{en_text}[/white]\n"
        f"  [cyan]{s_text}[/cyan]\n\n"
        f"  [dim]Primary translation ({lang_p}): {p_text}[/dim]",
        title="[dim]splash preview[/dim]",
        border_style="bright_black",
        padding=(0, 2),
    ))
    console.print()
    console.print(f"  [dim]Run [green]quran[/green] to see the full splash screen.[/dim]\n")
