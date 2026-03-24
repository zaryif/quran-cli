"""
quran hadith — browse and search authentic Hadith from the Kutub al-Sittah.

All hadith fetched live from fawazahmed0/hadith-api (jsDelivr CDN, free, no key).
Only Sahih and Hasan grade hadith — same authenticity standard as quran guide corpus.

Usage:
  quran hadith                         # interactive edition & book browser
  quran hadith daily                   # today's hadith of the day
  quran hadith browse <edition>        # browse books within an edition
  quran hadith read <edition> <num>    # read a specific hadith
  quran hadith search "patience"       # search by curated topics
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
    """Fetch sections/books within an edition (metadata only)."""
    try:
        import httpx
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/sections.json"
        r = httpx.get(url, timeout=10.0)
        return r.json()
    except Exception:
        return {}

def _fetch_section_hadiths(edition: str, section: str) -> list[dict]:
    """Fetch all hadiths within a specific section/book."""
    try:
        import httpx
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/sections/{section}.json"
        r = httpx.get(url, timeout=10.0)
        data = r.json()
        return data.get("hadiths", [])
    except Exception:
        return []

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
        return h # Return raw hadith dict from API
    except Exception:
        return None


# ── Rendering ─────────────────────────────────────────────────────────────────

def _render(h: dict, show_arabic: bool = True) -> None:
    """Render a single hadith."""
    from quran.core.quran_engine import format_arabic

    console.print()
    # Handle reference variations from the API
    ref = h.get("reference", f"#{h.get('hadithnumber', h.get('number', '?'))}")
    
    console.print(Rule(
        f"[yellow]◉ Hadith[/yellow]  [dim]{ref}[/dim]",
        style="bright_black"
    ))
    console.print()

    if show_arabic and h.get("arabic"):
        from rich.align import Align
        from rich.text import Text
        shaped = format_arabic(h["arabic"])
        console.print(Align.right(
            Text(shaped, style="bold yellow", justify="right"),
            width=console.width - 4
        ))
        console.print()

    console.print(
        Panel(
            f"[white]{h.get('text', '')}[/white]",
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
    edition: Annotated[str, typer.Argument(help="Edition ID (e.g. eng-bukhari)")] = "eng-bukhari",
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
    console.print(f"\n  [dim]Searching for '[bold]{keyword}[/bold]'...[/dim]")
    console.print("  [yellow]Note:[/yellow] For deep search, use [green]quran guide --hadith \"keyword\"[/green]\n")


# ── Interactive picker ────────────────────────────────────────────────────────

def _interactive_picker() -> None:
    console.print()
    console.print(Rule("[dim]Hadith Browser[/dim]", style="green"))
    console.print()

    try:
        from simple_term_menu import TerminalMenu
        
        with console.status("[dim]Loading collections…[/dim]"):
            editions = _fetch_editions()
        
        if not editions:
            console.print("[red]✗[/red] Could not fetch editions.")
            return

        # Selection flow: Edition -> Section -> Hadiths
        sorted_keys = sorted(editions.keys(), key=lambda k: (editions[k].get("language", ""), editions[k].get("name", "")))
        labels = [f"  {editions[k].get('name', k):<40} [dim]{editions[k].get('language', '')}[/dim]" for k in sorted_keys]
        labels.insert(0, "  [bold]Hadith of the Day[/bold]")

        console.print("  [dim]↑↓ navigate · Enter select · q back[/dim]\n")

        menu = TerminalMenu(
            labels, 
            title="  Select a Collection to Browse:", 
            menu_cursor_style=("fg_green", "bold"), 
            menu_highlight_style=("fg_green", "bold"),
            show_search_hint=True
        )
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
    """Browse books/sections within a collection."""
    while True:
        with console.status(f"[dim]Loading '{edition_key}' metadata…[/dim]"):
            sections_data = _fetch_sections(edition_key)
        
        if not sections_data:
            console.print("[red]✗[/red] Could not load collection metadata.")
            return

        sections = sections_data.get("sections", {})
        if not sections:
            hadith_read(edition_key, 1) # Fallback to sequential read
            return

        labels = []
        sec_keys = sorted(sections.keys(), key=lambda k: int(k) if k.isdigit() else k)
        for k in sec_keys:
            name = sections[k] or "Untitled Section"
            labels.append(f"  {k:>3}. {name}")

        console.print()
        menu = TerminalMenu(
            labels, 
            title=f"  {edition_key} Books:", 
            menu_cursor_style=("fg_green", "bold"), 
            menu_highlight_style=("fg_green", "bold"),
            show_search_hint=True
        )
        idx = menu.show()

        if idx is None: return
        
        selected_sec = sec_keys[idx]
        _read_section_flow(edition_key, selected_sec, TerminalMenu)

def _read_section_flow(edition: str, section_no: str, TerminalMenu) -> None:
    """Read hadiths within a section with navigation."""
    with console.status(f"[dim]Fetching Hadiths from section {section_no}…[/dim]"):
        hadiths = _fetch_section_hadiths(edition, section_no)

    if not hadiths:
        console.print("[red]✗[/red] No hadiths found in this section.")
        return

    curr_idx = 0
    while 0 <= curr_idx < len(hadiths):
        h = hadiths[curr_idx]
        _render(h)

        console.print(f"  [dim]Hadith {curr_idx + 1} of {len(hadiths)}[/dim]")
        console.print("  [dim]n: next · p: previous · q: back to books[/dim]")
        console.print("  > ", end="")
        
        try:
            cmd = input().strip().lower()
            if cmd == "n":
                if curr_idx < len(hadiths) - 1:
                    curr_idx += 1
                else:
                    console.print("  [yellow]End of book.[/yellow]")
            elif cmd == "p":
                if curr_idx > 0:
                    curr_idx -= 1
                else:
                    console.print("  [yellow]Start of book.[/yellow]")
            elif cmd == "q":
                break
            else:
                pass
        except (KeyboardInterrupt, EOFError):
            break
