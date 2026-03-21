"""
quran news — Muslim world news headlines via RSS.
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.rule import Rule
from typing_extensions import Annotated

app     = typer.Typer(help="Muslim world news headlines.")
console = Console()

FEEDS = {
    "aljazeera":  "https://www.aljazeera.com/xml/rss/all.xml",
    "seekers":    "https://seekersguidance.org/feed/",
    "5pillars":   "https://5pillarsuk.com/feed/",
    "islamqa":    "https://islamqa.info/en/feed",
}


@app.callback(invoke_without_command=True)
def news_cmd(
    ctx:    typer.Context,
    source: Annotated[str, typer.Option("--source", "-s",
            help="Feed: aljazeera, seekers, 5pillars, islamqa")] = "aljazeera",
    limit:  Annotated[int, typer.Option("--limit",  "-n")] = 8,
):
    if ctx.invoked_subcommand:
        return

    try:
        import feedparser
    except ImportError:
        console.print("[red]✗[/red] feedparser not installed: pip install feedparser")
        return

    url = FEEDS.get(source.lower(), FEEDS["aljazeera"])
    with console.status(f"[dim]Fetching {source} headlines…[/dim]"):
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            console.print(f"[red]✗[/red] Could not fetch feed: {e}")
            return

    entries = feed.entries[:limit]
    if not entries:
        console.print("[dim]No articles found. Check your connection.[/dim]")
        return

    console.print()
    console.print(Rule(f"[dim]{source}[/dim]", style="bright_black"))
    console.print()

    for i, e in enumerate(entries, 1):
        title   = getattr(e, "title", "No title")
        summary = getattr(e, "summary", "")[:160].strip()
        link    = getattr(e, "link", "")
        published = getattr(e, "published", "")[:16] if hasattr(e, "published") else ""

        console.print(f"  [green]{i:>2}[/green]  [bold white]{title}[/bold white]")
        if summary:
            console.print(f"      [dim]{summary}…[/dim]")
        if published:
            console.print(f"      [dim]{published}[/dim]")
        console.print()

    console.print(f"  [dim]Sources: {' · '.join(FEEDS.keys())}[/dim]")
    console.print(f"  [dim]quran news --source seekers --limit 5[/dim]\n")
