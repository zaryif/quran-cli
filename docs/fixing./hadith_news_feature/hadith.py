"""
quran hadith — Read authentic Hadith from the Kutub al-Sittah.

Data source: fawazahmed0/hadith-api (jsDelivr CDN)
Collections: Sahih Bukhari, Sahih Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah.
"""
from __future__ import annotations
import random
import re
import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Read authentic Hadith.")
console = Console()

HADITH_COLLECTIONS = {
    "bukhari":  "eng-bukhari",
    "muslim":   "eng-muslim",
    "abudawud": "eng-abudawud",
    "tirmidhi": "eng-tirmidhi",
    "nasai":    "eng-nasai",
    "ibnmajah": "eng-ibnmajah",
}

COLLECTION_NAMES = {
    "bukhari":  "Sahih Bukhari",
    "muslim":   "Sahih Muslim",
    "abudawud": "Abu Dawud",
    "tirmidhi": "Jami at-Tirmidhi",
    "nasai":    "Sunan an-Nasa'i",
    "ibnmajah": "Sunan Ibn Majah",
}

@app.callback(invoke_without_command=True)
def hadith_main(
    ctx: typer.Context,
    random_hadith: Annotated[bool, typer.Option("--random", "-r", help="Show a random Sahih Hadith")] = False,
):
    """Read authentic Hadith."""
    if ctx.invoked_subcommand:
        return

    if random_hadith:
        show_random()
    else:
        # Show help if no subcommand and no --random
        console.print()
        console.print(Panel(
            "[bold green]quran hadith[/bold green] — Read authentic Hadith.\n\n"
            "[dim]Data from the Kutub al-Sittah via fawazahmed0/hadith-api.[/dim]\n\n"
            "  [dim]quran hadith [/dim][green]random[/green]         [dim]← random Sahih hadith[/dim]\n"
            "  [dim]quran hadith [/dim][green]read bukhari 1[/green] [dim]← specific reference[/dim]\n\n"
            "  [dim]Collections: bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah[/dim]",
            border_style="green", padding=(1, 2),
        ))

@app.command("random")
def show_random():
    """Show a random Sahih Hadith."""
    col = random.choice(list(HADITH_COLLECTIONS.keys()))
    # Most collections have thousands of hadith. We'll pick a safe range for random.
    # Bukhari has ~7563, Muslim ~7500. We'll use a conservative range.
    num = random.randint(1, 100) # Simple start, can be improved with book/number mapping
    
    # Actually, fawazahmed0/hadith-api allows fetching by edition.
    # To be more robust, we'll pick from a known set of "best" hadith or just a random number.
    _fetch_and_print(col, 1, num) # Book 1, random number for now

@app.command("read")
def read_hadith(
    collection: Annotated[str, typer.Argument(help="bukhari|muslim|abudawud|tirmidhi|nasai|ibnmajah")],
    number:     Annotated[int, typer.Argument(help="Hadith number")],
    book:       Annotated[int, typer.Option("--book", "-b", help="Book number")] = 1,
):
    """Read a specific Hadith."""
    col = collection.lower()
    if col not in HADITH_COLLECTIONS:
        console.print(f"[red]✗[/red] Unknown collection: {collection}")
        console.print(f"  [dim]Valid: {', '.join(HADITH_COLLECTIONS.keys())}[/dim]")
        return
    
    _fetch_and_print(col, book, number)

def _fetch_and_print(col: str, book: int, num: int):
    edition = HADITH_COLLECTIONS[col]
    url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/{book}/{num}.json"
    
    with console.status(f"[dim]Fetching {COLLECTION_NAMES[col]} {book}:{num}…[/dim]"):
        try:
            r = httpx.get(url, timeout=10.0, follow_redirects=True)
            if r.status_code != 200:
                console.print(f"[red]✗[/red] Could not find hadith {num} in book {book} of {col.capitalize()}.")
                return
            data = r.json()
        except Exception as e:
            console.print(f"[red]✗[/red] Error fetching hadith: {e}")
            return

    hadiths = data.get("hadiths", [])
    if not hadiths:
        console.print("[red]✗[/red] No hadith content found.")
        return

    h = hadiths[0]
    arabic = h.get("arab", "")
    text   = h.get("text", "")
    
    # Clean up text
    text = re.sub(r"^it was narrated (that )?|^narrated [^:]+:", "", text, flags=re.I).strip()

    title = f"{COLLECTION_NAMES[col]} {book}:{num}"
    
    console.print()
    console.print(Rule(f"[bold green]{title}[/bold green]", style="bright_black"))
    console.print()
    
    if arabic:
        console.print(Panel(arabic, border_style="dim", padding=(1, 2)))
        console.print()
    
    console.print(text)
    console.print()
    console.print(f"  [dim]Source: fawazahmed0/hadith-api[/dim]")
    console.print()

