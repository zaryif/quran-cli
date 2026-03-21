"""
quran search — full-text search across the Quran.

Usage:
  quran search "patience"
  quran search "sabr" --lang ar
  quran search "light" --limit 10
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.text import Text
from typing_extensions import Annotated

app     = typer.Typer(help="Search across the Quran.")
console = Console()


@app.callback(invoke_without_command=True)
def search_cmd(
    ctx:   typer.Context,
    query: Annotated[str,  typer.Argument(help="Word or phrase to search")],
    lang:  Annotated[str,  typer.Option("--lang", "-l")] = "",
    limit: Annotated[int,  typer.Option("--limit", "-n")] = 20,
):
    if ctx.invoked_subcommand:
        return

    from quran.config.settings import load
    from quran.core.quran_engine import search_quran

    cfg  = load()
    lang = lang or cfg.get("lang", "en")

    with console.status(f"[dim]Searching for '{query}'…[/dim]"):
        results = search_quran(query, lang=lang, limit=limit)

    if not results:
        console.print(f"[dim]No results for [bold]{query}[/bold] in cached surahs.[/dim]")
        console.print("[dim]Tip: read a surah first to cache it, then search.[/dim]")
        return

    console.print(f"\n[dim]Found [bold green]{len(results)}[/bold green] results for '[bold]{query}[/bold]'[/dim]\n")

    for r in results:
        meta     = r.get("meta") or {}
        ref_str  = f"[green]{meta.get('name','?')} {r['surah']}:{r['ayah']}[/green]"
        text     = r["text"]
        # highlight query
        hi = text.replace(query, f"[bold yellow]{query}[/bold yellow]")
        console.print(f"  {ref_str}")
        console.print(f"  {hi}")
        console.print()
