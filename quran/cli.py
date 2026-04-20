"""quran-cli — Islamic terminal companion. Entry point: quran"""
import typer
from typing import Optional
from typing_extensions import Annotated
from rich.console import Console

app = typer.Typer(
    name="quran", help="[green]quran-cli[/green] — your Islamic terminal companion.",
    rich_markup_mode="rich", no_args_is_help=False,
    add_completion=True, pretty_exceptions_enable=False,
)
console = Console()

from quran import __version__
from quran.commands import (
    read, search, pray, remind, ramadan, eid, news,
    bookmark, tafsir, config as cfg_cmd, schedule, quote,
    streak, guide, connect, namaz, lang, gui, update, cache,
    hadith, bot, fasting, clock, lock,
)
app.add_typer(read.app,     name="read",     help="Read Quran by surah or ayah.")
app.add_typer(search.app,   name="search",   help="Search across the Quran.")
app.add_typer(pray.app,     name="pray",     help="Prayer times for your location.")
app.add_typer(remind.app,   name="remind",   help="Prayer & reading reminders.")
app.add_typer(ramadan.app,  name="ramadan",  help="Ramadan timings — sehri, iftar, tarawih.")
app.add_typer(eid.app,      name="eid",      help="Eid salah guide & details.")
app.add_typer(namaz.app,    name="namaz",    help="Prayer details & rakat breakdown.")
app.add_typer(lang.app,     name="lang",     help="Set display language and translations.")
app.add_typer(news.app,     name="news",     help="Muslim world news headlines.")
app.add_typer(hadith.app,   name="hadith",   help="Browse and search authentic Hadith.")
app.add_typer(bookmark.app, name="bookmark", help="Save and navigate reading positions.")
app.add_typer(tafsir.app,   name="tafsir",   help="Tafsir for any ayah.")
app.add_typer(cfg_cmd.app,  name="config",   help="Configure quran-cli settings.")
app.add_typer(schedule.app, name="schedule", help="Full day Islamic schedule view.")
app.add_typer(guide.app,    name="guide",    help="AI Quran & Hadith guide (RAG).")
app.add_typer(connect.app,  name="connect",  help="Notification channels.")
app.add_typer(update.app,   name="update",   help="Update quran-cli to the latest version.")
app.add_typer(cache.app,    name="cache",    help="Download Quran for offline use.")
app.add_typer(bot.app,      name="bot",      help="Telegram prayer reminder bot.")
app.add_typer(fasting.app,  name="fasting",  help="Daily fasting times — Sahur, Iftar & Sunnah days.")
app.add_typer(clock.app,   name="clock",    help="Live prayer clock with 5-waqt Namaz times and countdown.")
app.add_typer(lock.app,    name="lock",     help="Screen lock with optional PIN protection.")

@app.command("browse")
def browse_cmd(
    edition: Annotated[Optional[str], typer.Argument(help="Edition ID to browse")] = None
):
    """Interactive section browser for Hadith."""
    from quran.commands.hadith import _interactive_picker, _browse_edition_sections
    from simple_term_menu import TerminalMenu
    if edition:
        _browse_edition_sections(edition, TerminalMenu)
    else:
        _interactive_picker()

@app.command("quote")
def quote_cmd():
    """Show a random ayah quote."""
    quote.show_quote()

@app.command("streak")
def streak_cmd():
    """Show reading and fasting streak."""
    streak.show_streak()

@app.command("info")
def info_cmd(
    topic: str = typer.Argument("", help="surahs|methods|languages|hijri|location"),
    extra: str = typer.Argument("", help="Extra arg"),
):
    """Quick reference information."""
    from quran.core.quran_engine import list_surahs, get_surah_meta
    from quran.core.ramadan import gregorian_to_hijri
    from quran.core.location import detect_location
    from quran.core.prayer_times import METHODS
    from datetime import date
    if topic == "surahs":
        from rich.table import Table; from rich import box
        t = Table(box=box.SIMPLE, show_header=True, header_style="dim", border_style="bright_black", padding=(0,1))
        t.add_column("#",4); t.add_column("Name",18); t.add_column("Meaning",26,style="dim")
        t.add_column("Ayahs",7); t.add_column("Type",8,style="dim")
        for r in list_surahs(): t.add_row(str(r[0]),r[1],r[2],str(r[3]),r[4])
        console.print(); console.print(t)
    elif topic == "surah":
        n=int(extra) if extra.isdigit() else 1; m=get_surah_meta(n)
        if m: console.print(f"\n  [green]{m['name']}[/green]  [dim]{m['meaning']} · {m['ayahs']} ayahs · {m['type']}[/dim]\n")
    elif topic == "methods":
        [console.print(f"  [green]{k:<12}[/green]  [dim]{v['name']}[/dim]") for k,v in METHODS.items()]; console.print()
    elif topic == "hijri":
        hy,hm,hd=gregorian_to_hijri(date.today())
        months=["Muharram","Safar","Rabi al-Awwal","Rabi al-Thani","Jumada al-Awwal","Jumada al-Thani",
                "Rajab","Sha'ban","Ramadan","Shawwal","Dhul Qi'dah","Dhul Hijjah"]
        console.print(f"\n  [green]{hd} {months[hm-1]} {hy} AH[/green]\n")
    elif topic == "location":
        loc=detect_location()
        console.print(f"\n  [green]{loc.get('city')}, {loc.get('country')}[/green]  [dim]{loc.get('lat'):.4f}°N · {loc.get('lon'):.4f}°E[/dim]\n")
    else:
        console.print("\n  [dim]quran info surahs · surah 36 · methods · languages · hijri · location[/dim]\n")

@app.command("gui")
def gui_cmd():
    """Interactive terminal dashboard."""
    from quran.commands.gui import show_gui
    show_gui()


def version_callback(value: bool):
    if value:
        console.print(f"[bold green]quran-cli[/bold green] [dim]v{__version__}[/dim]")
        raise typer.Exit()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version and exit."),
):
    """[bold green]quran-cli[/bold green] — run [green]quran gui[/green], [green]quran schedule[/green] or [green]quran --help[/green]"""
    if ctx.invoked_subcommand is None:
        from quran.commands.gui import show_gui
        show_gui()
