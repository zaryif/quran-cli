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

v1.2.8: Structured browsing with correct API endpoints and in-memory cache.
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

# ── In-memory cache to avoid repeated API calls ──────────────────────────────

_cache: dict[str, object] = {}


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


# ── API fetch (with cache) ───────────────────────────────────────────────────

def _fetch_editions() -> dict:
    """
    Fetch all available hadith collections from editions.json.
    Returns dict: {collection_key: {name, collection: [...]}}
    Cached in memory after first call.
    """
    if "editions" in _cache:
        return _cache["editions"]
    try:
        import httpx
        url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json"
        r = httpx.get(url, timeout=15.0)
        data = r.json()
        _cache["editions"] = data
        return data
    except Exception:
        return {}


def _fetch_edition_metadata(edition: str) -> dict:
    """
    Fetch metadata for an edition (sections list + section names).
    Uses the main edition .min.json file and caches the sections only.
    Returns dict: {sections: {num: name}, name: str}
    """
    cache_key = f"meta:{edition}"
    if cache_key in _cache:
        return _cache[cache_key]
    try:
        import httpx
        # Use .min.json for smaller payload (still contains full metadata)
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}.min.json"
        r = httpx.get(url, timeout=30.0, follow_redirects=True)
        data = r.json()
        meta = data.get("metadata", {})
        result = {
            "name":     meta.get("name", edition),
            "sections": meta.get("sections", {}),
        }
        _cache[cache_key] = result
        return result
    except Exception:
        return {"name": edition, "sections": {}}


def _fetch_section_hadiths(edition: str, section: str) -> list[dict]:
    """
    Fetch all hadiths within a specific section (lightweight, ~16KB).
    Returns list of hadith dicts.
    """
    cache_key = f"sec:{edition}:{section}"
    if cache_key in _cache:
        return _cache[cache_key]
    try:
        import httpx
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/sections/{section}.json"
        r = httpx.get(url, timeout=15.0)
        if r.status_code != 200:
            return []
        data = r.json()
        hadiths = data.get("hadiths", [])
        _cache[cache_key] = hadiths
        return hadiths
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
        r = httpx.get(url, timeout=15.0)
        if r.status_code != 200:
            return None
        data = r.json()
        hadiths = data.get("hadiths", [])
        if not hadiths:
            return None
        return hadiths[0]
    except Exception:
        return None


# ── Rendering ─────────────────────────────────────────────────────────────────

def _render(h: dict, show_arabic: bool = True) -> None:
    """Render a single hadith with optional Arabic text."""
    num = h.get("hadithnumber", h.get("number", "?"))

    console.print()
    console.print(Rule(
        f"[yellow]◉ Hadith #{num}[/yellow]",
        style="bright_black"
    ))
    console.print()

    # Arabic text (key varies: "arabic", "arab", or missing)
    arabic = h.get("arabic", h.get("arab", ""))
    if show_arabic and arabic:
        try:
            from quran.core.quran_engine import format_arabic
            from rich.align import Align
            from rich.text import Text
            shaped = format_arabic(arabic)
            console.print(Align.right(
                Text(shaped, style="bold yellow", justify="right"),
                width=console.width - 4
            ))
            console.print()
        except Exception:
            pass

    text = h.get("text", "")
    if text:
        console.print(
            Panel(
                f"[white]{text}[/white]",
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
    collections = ["eng-bukhari", "eng-muslim", "eng-abudawud",
                   "eng-tirmidhi", "eng-nasai", "eng-ibnmajah"]
    col_idx = (date.today().day - 1) % len(collections)
    edition = collections[col_idx]
    num = (date.today().day * 7) % 100 + 1

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

    table = Table(box=box.SIMPLE, show_header=True,
                  header_style="dim", border_style="bright_black")
    table.add_column("Edition ID", width=20)
    table.add_column("Language", width=12)
    table.add_column("Author", width=20, style="dim")
    table.add_column("Collection", width=25)

    for coll_key, coll_data in sorted(editions.items()):
        coll_name = coll_data.get("name", coll_key)
        for ed in coll_data.get("collection", []):
            table.add_row(
                ed.get("name", ""),
                ed.get("language", ""),
                ed.get("author", ""),
                coll_name,
            )

    console.print(table)


@app.command("browse")
def hadith_browse(
    edition: Annotated[str, typer.Argument(
        help="Edition ID (e.g. eng-bukhari)"
    )] = "eng-bukhari"
):
    """Interactive section browser for an edition."""
    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        console.print("  [red]simple-term-menu[/red] required for interactive browser.")
        return
    _browse_edition_sections(edition, TerminalMenu)


@app.command("read")
def hadith_read(
    edition: Annotated[str, typer.Argument(
        help="Edition ID (e.g. eng-bukhari)"
    )] = "eng-bukhari",
    number: Annotated[int, typer.Argument(help="Hadith number")] = 1,
    no_arabic: Annotated[bool, typer.Option(
        "--no-arabic", help="Hide Arabic text"
    )] = False,
):
    """Read a specific hadith with n/p/q navigation."""
    num = number
    while True:
        with console.status(f"[dim]Fetching {edition} #{num}…[/dim]"):
            h = _fetch_hadith(edition, num)

        if not h:
            console.print(f"[red]✗[/red] Hadith {num} not found.")
            break

        _render(h, show_arabic=not no_arabic)

        console.print("  [dim]n: next · p: previous · q: exit[/dim]")
        console.print("  > ", end="")
        try:
            key = input().strip().lower()
            if key == "n":
                num += 1
            elif key == "p":
                num = max(1, num - 1)
            elif key == "q":
                break
            else:
                break
        except (KeyboardInterrupt, EOFError):
            break


@app.command("search")
def hadith_search(
    keyword: Annotated[str, typer.Argument(
        help="Keyword to search (curated topics)"
    )],
    limit: Annotated[int, typer.Option("--limit", "-n")] = 5,
):
    """Search hadith by curated topic keyword."""
    kw = keyword.lower().strip()
    matched = {t: refs for t, refs in HADITH_TOPICS.items() if kw in t}

    if not matched:
        console.print(f"\n  [yellow]No curated topic matching '{keyword}'.[/yellow]")
        console.print("  [dim]Available topics:[/dim]")
        console.print(f"  [dim]{', '.join(sorted(HADITH_TOPICS.keys()))}[/dim]\n")
        console.print("  [dim]For deep search: [green]quran guide --hadith \"keyword\"[/green][/dim]\n")
        return

    for topic, refs in matched.items():
        console.print(f"\n  [green]◉ {topic.title()}[/green]")
        for coll, book, num in refs[:limit]:
            edition = f"eng-{coll}"
            with console.status(f"[dim]Fetching {edition} #{num}…[/dim]"):
                h = _fetch_hadith(edition, num)
            if h:
                _render(h)


# ── Interactive picker ────────────────────────────────────────────────────────

def _interactive_picker() -> None:
    """Top-level interactive Hadith browser: Collection → Section → Read."""
    console.print()
    console.print(Rule("[dim]Hadith Browser[/dim]", style="green"))
    console.print()

    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        console.print("  [red]simple-term-menu[/red] required for interactive browser.")
        return

    with console.status("[dim]Loading collections…[/dim]"):
        editions = _fetch_editions()

    if not editions:
        console.print("[red]✗[/red] Could not fetch editions.")
        return

    # Build flat list of editions with collection names
    ed_items = []  # (edition_id, display_label)
    for coll_key, coll_data in sorted(editions.items()):
        coll_name = coll_data.get("name", coll_key)
        for ed in coll_data.get("collection", []):
            eid  = ed.get("name", "")
            lang = ed.get("language", "")
            ed_items.append((eid, f"  {coll_name:<30} {eid:<20} [{lang}]"))

    labels = [item[1] for item in ed_items]
    labels.insert(0, "  ★ Hadith of the Day")

    console.print("  [dim]↑↓ navigate · Enter select · / search · q back[/dim]\n")

    menu = TerminalMenu(
        labels,
        title="  Select a Collection to Browse:",
        menu_cursor="> ",
        menu_cursor_style=("fg_green", "bold"),
        menu_highlight_style=("fg_green", "bold"),
        show_search_hint=True,
    )
    idx = menu.show()

    if idx is None:
        return
    if idx == 0:
        hadith_daily()
        return

    edition_key = ed_items[idx - 1][0]
    _browse_edition_sections(edition_key, TerminalMenu)


def _browse_edition_sections(edition_key: str, TerminalMenu) -> None:
    """Browse books/sections within a collection."""
    with console.status(f"[dim]Loading '{edition_key}' books…[/dim]"):
        meta = _fetch_edition_metadata(edition_key)

    sections = meta.get("sections", {})
    coll_name = meta.get("name", edition_key)

    if not sections:
        # No sections available — fallback to sequential reading
        console.print(f"  [yellow]No sections found for {edition_key}. Starting sequential read.[/yellow]")
        hadith_read(edition_key, 1)
        return

    # Build section menu (skip section "0" which is usually empty)
    sec_keys = sorted(
        [k for k in sections.keys() if k != "0"],
        key=lambda k: int(k) if k.isdigit() else 0
    )
    labels = []
    for k in sec_keys:
        name = sections[k] or "General"
        labels.append(f"  {k:>3}. {name}")

    while True:
        console.print()
        console.print(Rule(
            f"[dim]{coll_name}[/dim]  [green]{len(sec_keys)} books[/green]",
            style="bright_black"
        ))
        console.print("  [dim]↑↓ navigate · Enter select · / search · q back[/dim]\n")

        menu = TerminalMenu(
            labels,
            title=f"  {coll_name} — Select a Book:",
            menu_cursor="> ",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green", "bold"),
            show_search_hint=True,
        )
        idx = menu.show()

        if idx is None:
            return

        selected_sec = sec_keys[idx]
        sec_name = sections.get(selected_sec, "")
        _read_section_flow(edition_key, selected_sec, sec_name)


def _read_section_flow(edition: str, section_no: str, section_name: str) -> None:
    """Read hadiths within a section with n/p/q navigation."""
    with console.status(f"[dim]Loading Book {section_no}: {section_name}…[/dim]"):
        hadiths = _fetch_section_hadiths(edition, section_no)

    if not hadiths:
        console.print(f"[red]✗[/red] No hadiths found in section {section_no}.")
        return

    curr = 0
    total = len(hadiths)

    while 0 <= curr < total:
        h = hadiths[curr]
        _render(h)

        console.print(f"  [dim]Book {section_no}: {section_name}  ·  {curr + 1}/{total}[/dim]")
        console.print("  [dim]n: next · p: previous · q: back to books[/dim]")
        console.print("  > ", end="")

        try:
            cmd = input().strip().lower()
            if cmd == "n":
                if curr < total - 1:
                    curr += 1
                else:
                    console.print("  [yellow]End of book.[/yellow]")
            elif cmd == "p":
                if curr > 0:
                    curr -= 1
                else:
                    console.print("  [yellow]Start of book.[/yellow]")
            elif cmd == "q":
                break
            else:
                pass
        except (KeyboardInterrupt, EOFError):
            break
