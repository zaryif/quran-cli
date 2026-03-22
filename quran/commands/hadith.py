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

def _fetch_hadith(collection: str, book: int, number: int) -> Optional[dict]:
    """
    Fetch a single hadith from fawazahmed0/hadith-api (jsDelivr CDN).
    Source: https://github.com/fawazahmed0/hadith-api
    Returns dict or None on failure.
    """
    try:
        import httpx
        edition = COLLECTION_IDS.get(collection)
        if not edition:
            return None
        url = (
            f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/"
            f"editions/{edition}/{book}/{number}.json"
        )
        r    = httpx.get(url, timeout=10.0, follow_redirects=True)
        data = r.json()
        hadiths = data.get("hadiths", [])
        if not hadiths:
            return None
        h    = hadiths[0]
        text = h.get("text", "").strip()
        if not text:
            return None
        return {
            "text":      text,
            "arab":      h.get("arab", ""),
            "number":    h.get("number", number),
            "collection": COLLECTION_NAMES.get(collection, collection),
            "reference": f"{COLLECTION_NAMES.get(collection, collection)} {book}:{number}",
            "col_key":   collection,
            "book":      book,
        }
    except Exception:
        return None


# ── Rendering ─────────────────────────────────────────────────────────────────

def _render(h: dict, show_arabic: bool = True) -> None:
    """Render a single hadith — mirrors the ayah rendering style."""
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
        shaped = format_arabic(h["arab"][:400])
        console.print(Align.right(
            Text(shaped, style="bold yellow", justify="right"),
            width=console.width - 4
        ))
        console.print()

    console.print(
        Panel(
            f"[white]{h['text']}[/white]\n\n"
            f"[dim green]— {h['reference']}  (Sahih)[/dim green]",
            title="[dim]hadith[/dim]",
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
    idx = (date.today().day - 1) % len(_DAILY)
    col, book, num = _DAILY[idx]

    with console.status("[dim]Fetching today's hadith…[/dim]"):
        h = _fetch_hadith(col, book, num)

    if not h:
        console.print("[red]✗[/red] Could not fetch hadith. Check your internet connection.")
        return

    console.print()
    console.print(Rule("[bold]Hadith of the Day[/bold]", style="bright_black"))
    _render(h)
    console.print(
        f"  [dim]Browse by topic: [green]quran hadith topics[/green]  ·  "
        f"Search: [green]quran hadith search <topic>[/green][/dim]\n"
    )


@app.command("topics")
def hadith_topics():
    """List all available hadith topic categories."""
    console.print()
    console.print(Rule("[dim]Hadith topics[/dim]", style="bright_black"))
    console.print()

    table = Table(
        box=box.SIMPLE, show_header=True, header_style="dim",
        border_style="bright_black", padding=(0, 2),
    )
    table.add_column("Topic",       width=18)
    table.add_column("Hadith",      width=8)
    table.add_column("Collection",  width=34, style="dim")

    for topic, refs in HADITH_TOPICS.items():
        cols = ", ".join(COLLECTION_NAMES.get(r[0], r[0]) for r in refs)
        table.add_row(topic, str(len(refs)), cols)

    console.print(table)
    console.print(f"  [dim]quran hadith search <topic>   [/dim]"
                  f"[dim]to read hadith on a topic[/dim]\n")


@app.command("read")
def hadith_read(
    collection: Annotated[str, typer.Argument(
        help="Collection: bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah"
    )] = "bukhari",
    book:       Annotated[int, typer.Argument(help="Book number")] = 1,
    number:     Annotated[int, typer.Argument(help="Hadith number")] = 1,
    no_arabic:  Annotated[bool, typer.Option(
        "--no-arabic", help="Hide Arabic text"
    )] = False,
):
    """Read a specific hadith by collection, book, and number."""
    col = collection.lower().strip()
    if col not in COLLECTION_IDS:
        console.print(
            f"[red]✗[/red] Unknown collection '[bold]{col}[/bold]'.\n"
            f"  Options: {', '.join(COLLECTION_IDS.keys())}"
        )
        return

    with console.status(
        f"[dim]Fetching {COLLECTION_NAMES.get(col, col)} {book}:{number}…[/dim]"
    ):
        h = _fetch_hadith(col, book, num=number)

    if not h:
        console.print(
            f"[red]✗[/red] Could not fetch {col} {book}:{number}.\n"
            f"  [dim]The hadith may not exist at this reference.[/dim]"
        )
        return

    _render(h, show_arabic=not no_arabic)


@app.command("search")
def hadith_search(
    keyword: Annotated[str, typer.Argument(help="Topic or keyword to search")],
    limit:   Annotated[int, typer.Option("--limit", "-n")] = 5,
):
    """Search hadith by topic keyword."""
    kw = keyword.lower().strip()

    # Collect matches — exact then partial
    matches: list[tuple[str, int, int]] = []
    for topic, refs in HADITH_TOPICS.items():
        if kw == topic or kw in topic or topic in kw:
            matches.extend(refs)
        elif any(kw in part for part in topic.split("-")):
            matches.extend(refs)

    # Deduplicate
    seen:   set[tuple] = set()
    unique: list[tuple[str, int, int]] = []
    for r in matches:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    if not unique:
        console.print(
            f"\n  [dim]No topic matches for '[bold]{keyword}[/bold]'.[/dim]\n"
            f"  [dim]Run [green]quran hadith topics[/green] for a full list.[/dim]\n"
            f"  [dim]For AI search: [green]quran guide --hadith \"{keyword}\"[/green][/dim]\n"
        )
        return

    console.print()
    console.print(Rule(f"[dim]hadith · {keyword}[/dim]", style="bright_black"))
    console.print()

    shown = 0
    for col, book, num in unique[:limit]:
        with console.status(
            f"[dim]Fetching {COLLECTION_NAMES.get(col, col)} {book}:{num}…[/dim]"
        ):
            h = _fetch_hadith(col, book, num)
        if h:
            _render(h, show_arabic=False)
            shown += 1

    if shown == 0:
        console.print(
            "  [dim]Could not fetch hadith. Check your internet connection.[/dim]\n"
        )
    else:
        console.print(
            f"  [dim]Showing {shown} result(s) for '[bold]{keyword}[/bold]'.[/dim]"
        )
        console.print(
            f"  [dim]AI-powered search: [green]quran guide --hadith \"{keyword}\"[/green][/dim]\n"
        )


# ── Interactive picker ────────────────────────────────────────────────────────

def _interactive_picker() -> None:
    console.print()
    console.print(Rule("[dim]Hadith[/dim]", style="green"))
    console.print()

    topic_list = list(HADITH_TOPICS.keys())

    try:
        from simple_term_menu import TerminalMenu

        labels = []
        for t in topic_list:
            n = len(HADITH_TOPICS[t])
            labels.append(f"{t:<18s}  {n} hadith")
        labels.insert(0, "Today's hadith of the day")

        console.print("  [dim]↑↓ to navigate · Enter to select · q to cancel[/dim]\n")

        menu = TerminalMenu(
            labels,
            title="  Select a topic:",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green", "bold"),
        )
        idx = menu.show()

        if idx is None:
            console.print("  [dim]Cancelled.[/dim]")
            return

        if idx == 0:
            hadith_daily()
            return

        topic = topic_list[idx - 1]
        console.print(f"\n  [dim]Loading [bold]{topic}[/bold]…[/dim]\n")
        for col, book, num in HADITH_TOPICS[topic]:
            with console.status(
                f"[dim]Fetching {COLLECTION_NAMES.get(col, col)} {book}:{num}…[/dim]"
            ):
                h = _fetch_hadith(col, book, num)
            if h:
                _render(h)

    except ImportError:
        # Fallback: numbered list
        console.print("  [dim]Select a topic:[/dim]")
        console.print("   0  Today's hadith of the day")
        for i, t in enumerate(topic_list, 1):
            n = len(HADITH_TOPICS[t])
            console.print(f"  [green]{i:2d}[/green]  {t}  [dim]({n})[/dim]")
        console.print()
        console.print("[dim]Enter number:[/dim] ", end="")
        try:
            raw = input().strip()
            if raw == "0":
                hadith_daily()
                return
            n = int(raw) - 1
            if 0 <= n < len(topic_list):
                topic = topic_list[n]
                for col, book, num in HADITH_TOPICS[topic]:
                    with console.status("[dim]Fetching…[/dim]"):
                        h = _fetch_hadith(col, book, num)
                    if h:
                        _render(h)
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            console.print("[dim]Cancelled.[/dim]")
