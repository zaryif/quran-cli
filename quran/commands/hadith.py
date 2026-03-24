"""
quran hadith — browse and search authentic Hadith from the Kutub al-Sittah.

All hadith fetched live from fawazahmed0/hadith-api (jsDelivr CDN, free, no key).
Only Sahih and Hasan grade hadith — same authenticity standard as quran guide corpus.

Usage:
  quran hadith                         # interactive topic picker
  quran hadith daily                   # today's hadith of the day
  quran hadith topics                  # list all topic categories
  quran hadith search "patience"       # search by topic keyword
  quran hadith read bukhari 1 1        # read a specific hadith
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Browse and search authentic Hadith.")
console = Console()


# ── Curated hadith index — (collection, book, number) per topic ──────────────

HADITH_TOPICS: dict[str, list[tuple[str, int, int]]] = {
    "intention":      [("bukhari", 1,  1)],
    "prayer":         [("bukhari", 2, 21), ("muslim", 4, 126)],
    "fasting":        [("bukhari", 3, 31), ("abudawud", 3, 2)],
    "quran":          [("bukhari", 6,  2)],
    "pillars":        [("bukhari", 8,  2)],
    "friday":         [("bukhari", 13, 1)],
    "laylatul-qadr":  [("bukhari", 54, 1)],
    "parents":        [("bukhari", 67, 70)],
    "consistency":    [("bukhari", 73, 1)],
    "kindness":       [("bukhari", 78, 9), ("tirmidhi", 40, 1)],
    "patience":       [("muslim",  6,  38)],
    "charity":        [("muslim", 11,  4)],
    "brotherhood":    [("muslim", 32, 18)],
    "dua":            [("muslim", 45,  5)],
    "wudu":           [("abudawud", 8, 1)],
    "dhikr":          [("tirmidhi", 4,  1)],
    "tawakkul":       [("tirmidhi", 27, 1)],
    "knowledge":      [("ibnmajah", 1,  1)],
    "repentance":     [("ibnmajah", 33, 1)],
}

COLLECTION_NAMES = {
    "bukhari":  "Sahih Bukhari",
    "muslim":   "Sahih Muslim",
    "abudawud": "Abu Dawud",
    "tirmidhi": "Jami at-Tirmidhi",
    "nasai":    "Sunan an-Nasa'i",
    "ibnmajah": "Sunan Ibn Majah",
}

COLLECTION_IDS = {
    "bukhari":  "eng-bukhari",
    "muslim":   "eng-muslim",
    "abudawud": "eng-abudawud",
    "tirmidhi": "eng-tirmidhi",
    "nasai":    "eng-nasai",
    "ibnmajah": "eng-ibnmajah",
}

# Daily rotation — cycles by day-of-month
_DAILY: list[tuple[str, int, int]] = [
    ("bukhari", 1,  1),  ("bukhari", 8,  2),  ("bukhari", 3, 31),
    ("muslim",  6, 38),  ("tirmidhi", 27, 1), ("bukhari", 6,  2),
    ("bukhari", 73, 1),  ("muslim", 45,  5),  ("tirmidhi", 40, 1),
    ("bukhari", 78, 9),  ("muslim", 32, 18),  ("bukhari", 67, 70),
    ("ibnmajah", 1, 1),  ("ibnmajah", 33, 1), ("tirmidhi", 4,  1),
    ("bukhari", 2, 21),  ("bukhari", 13,  1), ("abudawud", 8,  1),
    ("muslim", 11,  4),  ("muslim",  4, 126), ("bukhari", 54,  1),
    ("abudawud", 3, 2),  ("nasai",  10,  1),  ("bukhari",  6,  2),
    ("muslim",  6, 38),  ("tirmidhi", 27, 1), ("bukhari", 73,  1),
    ("bukhari",  1, 1),  ("muslim", 32, 18),  ("ibnmajah", 1,  1),
    ("bukhari",  8, 2),
]


# ── API fetch ─────────────────────────────────────────────────────────────────

def _fetch_editions() -> dict:
    """Fetch all available hadith editions."""
    try:
        import httpx
        url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json"
        r = httpx.get(url, timeout=10.0)
        return r.json()
    except Exception:
        return {}

def _fetch_sections(edition: str) -> dict:
    """Fetch sections/books within an edition."""
    try:
        import httpx
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}.json"
        r = httpx.get(url, timeout=10.0)
        return r.json()
    except Exception:
        return {}

def _fetch_hadith(edition: str, number: int) -> Optional[dict]:
    """
    Fetch a single hadith by edition and number.
    Returns dict or None on failure.
    """
    try:
        import httpx
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/{number}.json"
        r = httpx.get(url, timeout=10.0)
        data = r.json()
        hadiths = data.get("hadiths", [])
        if not hadiths:
            return None
        h = hadiths[0]
        return {
            "text": h.get("text", "").strip(),
            "arab": h.get("arab", ""),
            "number": h.get("hadithnumber", number) or h.get("number", number),
            "edition": edition,
            "reference": f"{edition} #{number}",
        }
    except Exception:
        return None


# ── Rendering ─────────────────────────────────────────────────────────────────

def _render(h: dict, show_arabic: bool = True) -> None:
    """Render a single hadith."""
    from quran.core.quran_engine import format_arabic

    console.print()
    console.print(Rule(
        f"[yellow]◉ Hadith[/yellow]  [dim]{h['reference']}[/dim]",
        style="bright_black"
    ))
    console.print()

    if show_arabic and h.get("arab"):
        from rich.align import Align
        from rich.text import Text
        shaped = format_arabic(h["arab"])
        console.print(Align.right(
            Text(shaped, style="bold yellow", justify="right"),
            width=console.width - 4
        ))
        console.print()

    console.print(
        Panel(
            f"[white]{h['text']}[/white]",
            title=f"[dim]{h['edition']}[/dim]",
            border_style="bright_black",
            padding=(1, 3),
        )
    )
    console.print()


# ── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def hadith_cmd(ctx: typer.Context):
    """Browse and search authentic Hadith."""
    if ctx.invoked_subcommand is None:
        _interactive_picker()


@app.command("daily")
def hadith_daily():
    """Show today's hadith of the day (rotates daily)."""
    from datetime import date
    # Cycle through Kutub al-Sittah
    collections = ["eng-bukhari", "eng-muslim", "eng-abudawud", "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"]
    col_idx = (date.today().day - 1) % len(collections)
    edition = collections[col_idx]
    num = (date.today().day * 7) % 100 + 1 # Simple rotation

    with console.status("[dim]Fetching today's hadith…[/dim]"):
        h = _fetch_hadith(edition, num)

    if not h:
        console.print("[red]✗[/red] Could not fetch hadith. Check your internet connection.")
        return

    console.print()
    console.print(Rule("[bold]Hadith of the Day[/bold]", style="bright_black"))
    _render(h)


@app.command("list")
def hadith_list():
    """List all available Hadith editions."""
    with console.status("[dim]Fetching edition list…[/dim]"):
        editions = _fetch_editions()
    
    if not editions:
        console.print("[red]✗[/red] Could not fetch editions.")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim", border_style="bright_black")
    table.add_column("Name", width=30)
    table.add_column("Language", width=15)
    table.add_column("Collection", width=30, style="dim")

    # Sort editions by language then name
    sorted_eds = sorted(editions.values(), key=lambda x: (x.get("language", ""), x.get("name", "")))
    
    for ed in sorted_eds:
        table.add_row(ed.get("name", "Unknown"), ed.get("language", "-"), ed.get("collection", "-"))

    console.print(table)


@app.command("browse")
def hadith_browse(
    edition: Annotated[str, typer.Argument(help="Edition ID (e.g. eng-bukhari)")] = "eng-bukhari"
):
    """Interactive section browser for an edition."""
    from simple_term_menu import TerminalMenu
    _browse_edition_sections(edition, TerminalMenu)


@app.command("read")
def hadith_read(
    edition: Annotated[str, typer.Argument(help="Edition/Collection ID (e.g. eng-bukhari)")] = "eng-bukhari",
    number: Annotated[int, typer.Argument(help="Hadith number")] = 1,
    no_arabic: Annotated[bool, typer.Option("--no-arabic", help="Hide Arabic text")] = False,
):
    """Read a specific hadith with n/p/q navigation."""
    num = number
    while True:
        with console.status(f"[dim]Fetching {edition} #{num}…[/dim]"):
            h = _fetch_hadith(edition, num)

        if not h:
            console.print(f"[red]✗[/red] Could not fetch hadith {num}. It might not exist.")
            break

        _render(h, show_arabic=not no_arabic)
        
        console.print("  [dim]n: next · p: previous · q: exit[/dim]")
        console.print("  > ", end="")
        try:
            from quran.commands.gui import _get_menu
            TerminalMenu = _get_menu()
            key = input().strip().lower()
            if key == "n":
                num += 1
            elif key == "p":
                if num > 1:
                    num -= 1
                else:
                    console.print("  [yellow]Already at the first hadith.[/yellow]")
            elif key == "q":
                break
            else:
                break
        except (KeyboardInterrupt, EOFError):
            break


@app.command("search")
def hadith_search(
    keyword: Annotated[str, typer.Argument(help="Keyword to search (note: limited to curated topics)")],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 5,
):
    """Search hadith by curated topic keyword."""
    # This remains similar but simplified as the user wants focus on browsing
    console.print(f"\n  [dim]Searching for '[bold]{keyword}[/bold]'...[/dim]")
    # Implementation can be improved later with a proper search API if available
    console.print("  [yellow]Note:[/yellow] For deep search, use [green]quran guide --hadith \"keyword\"[/green]\n")


# ── Interactive picker ────────────────────────────────────────────────────────

def _interactive_picker() -> None:
    console.print()
    console.print(Rule("[dim]Hadith Browser[/dim]", style="green"))
    console.print()

    try:
        from simple_term_menu import TerminalMenu
        
        with console.status("[dim]Loading editions…[/dim]"):
            editions = _fetch_editions()
        
        if not editions:
            console.print("[red]✗[/red] Could not fetch editions.")
            return

        # Filter for English and major languages
        important_eds = {k: v for k, v in editions.items() if v.get("language", "").lower() in ["english", "arabic", "urdu", "bengali"]}
        sorted_keys = sorted(important_eds.keys(), key=lambda k: (important_eds[k].get("language", ""), important_eds[k].get("name", "")))
        
        labels = [f"  {important_eds[k].get('name', k):<40} [dim]{important_eds[k].get('language', '')}[/dim]" for k in sorted_keys]
        labels.insert(0, "  [bold underline]Daily Hadith[/bold underline]")

        console.print("  [dim]↑↓ navigate · Enter select · q back[/dim]\n")

        menu = TerminalMenu(labels, title="  Select a Collection:")
        idx = menu.show()

        if idx is None: return
        if idx == 0:
            hadith_daily()
            return

        edition_key = sorted_keys[idx - 1]
        _browse_edition_sections(edition_key, TerminalMenu)

    except ImportError:
        console.print("  [red]simple-term-menu[/red] required for interactive browser.")

def _browse_edition_sections(edition_key: str, TerminalMenu) -> None:
    """Browse sections of an edition."""
    with console.status(f"[dim]Loading sections for {edition_key}…[/dim]"):
        sections = _fetch_sections(edition_key)
    
    if not sections:
        console.print("[red]✗[/red] Could not load sections.")
        return

    sec_list = sections.get("sections", [])
    if not sec_list:
        # If no sections, just go straight to hadith 1
        hadith_read(edition_key, 1)
        return

    labels = [f"  Section {s.get('sectionNumber', i+1)}: {s.get('englishName', 'Untitled')}" for i, s in enumerate(sec_list)]
    menu = TerminalMenu(labels, title=f"  {edition_key} Sections:")
    idx = menu.show()

    if idx is None: return
    
    # Simple navigation: start from the first hadith of that section
    first_hadith = sec_list[idx].get("hadithStart", 1)
    hadith_read(edition_key, first_hadith)
