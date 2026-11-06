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
        import ssl
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context
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
        console.print("[dim]No articles found. Check your connection or feed URL.[/dim]")
        return

    from rich.panel import Panel
    from rich.text import Text

    console.print()
    console.print(Rule(f"[bold green]Muslim World News — {source.capitalize()}[/bold green]", style="green"))
    console.print()

    for i, e in enumerate(entries, 1):
        title   = getattr(e, "title", "No title")
        # Clean HTML completely for better terminal UI
        import re
        raw_summary = getattr(e, "summary", "")
        summary = re.sub('<[^<]+?>', '', raw_summary)[:200].strip()
        link    = getattr(e, "link", "")
        published = getattr(e, "published", "")[:16] if hasattr(e, "published") else ""

        title_text = Text(f"{i:>2}. {title}", style="bold white")
        
        body_text = Text()
        if summary:
            body_text.append(f"{summary}…\n", style="dim")
        if published:
            body_text.append(f"\n{published}  ", style="cyan")
        if link:
            body_text.append(f"🔗 {link}", style="blue underline")

        console.print(Panel(body_text, title=title_text, title_align="left", border_style="bright_black"))

    console.print(f"  [dim]Sources: {' · '.join(FEEDS.keys())}[/dim]")
    console.print(f"  [dim]quran news --source seekers --limit 5[/dim]\n")
