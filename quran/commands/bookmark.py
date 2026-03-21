"""
quran bookmark — save and navigate reading positions.
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Save and navigate reading positions.")
console = Console()


@app.callback(invoke_without_command=True)
def bookmark_cmd(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        list_bookmarks()


@app.command("save")
def save_bookmark(
    label: Annotated[str,           typer.Argument(help="Bookmark name e.g. 'fajr'")],
    ref:   Annotated[Optional[str], typer.Argument(help="Surah:ayah e.g. 18:1")] = None,
    note:  Annotated[str,           typer.Option("--note", "-n")] = "",
):
    """Save current or specified position."""
    from quran.core.bookmark_store import save_bookmark as _save

    if not ref:
        console.print("[dim]Provide a ref: quran bookmark save 'fajr' 18:1[/dim]")
        return

    try:
        s, a = ref.split(":", 1)
        surah, ayah = int(s), int(a)
    except ValueError:
        console.print(f"[red]✗[/red] Invalid ref: {ref}  (use surah:ayah format)")
        return

    _save(label, surah, ayah, note)
    console.print(f"[green]✓[/green] Saved '[bold]{label}[/bold]' → {surah}:{ayah}")


@app.command("goto")
def goto_bookmark(
    label: Annotated[str, typer.Argument(help="Bookmark name")],
    lang:  Annotated[str, typer.Option("--lang", "-l")] = "",
):
    """Jump to a saved bookmark and start reading."""
    from quran.core.bookmark_store import get_bookmark
    from quran.config.settings import load

    cfg  = load()
    lang = lang or cfg.get("lang", "en")
    bm   = get_bookmark(label)

    if not bm:
        console.print(f"[red]✗[/red] No bookmark named '{label}'.")
        return

    console.print(f"[dim]→ jumping to [bold]{label}[/bold] — {bm['surah']}:{bm['ayah']}[/dim]\n")

    from quran.core.quran_engine import fetch_surah, get_surah_meta
    from quran.ui.renderer import render_surah_header

    meta = get_surah_meta(bm["surah"])
    if meta:
        render_surah_header(meta)

    with console.status("[dim]Loading…[/dim]"):
        ayahs = fetch_surah(bm["surah"], lang, bm["ayah"], min(bm["ayah"] + 9, meta["ayahs"] if meta else bm["ayah"] + 9))

    for a in ayahs:
        console.print(f"  [dim green]{a['surah']}:{a['ayah']}[/dim green]  {a['text']}")
        console.print()


@app.command("list")
def list_bookmarks():
    """List all saved bookmarks."""
    from quran.core.bookmark_store import list_bookmarks as _list

    bms = _list()
    if not bms:
        console.print("[dim]No bookmarks yet. Use: quran bookmark save 'name' 2:255[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim",
                  border_style="bright_black", padding=(0,2))
    table.add_column("Label",  width=14)
    table.add_column("Surah",  width=6)
    table.add_column("Ayah",   width=6)
    table.add_column("Note",   width=24, style="dim")
    table.add_column("Saved",  width=20, style="dim")

    for label, b in bms.items():
        table.add_row(
            f"[green]{label}[/green]",
            str(b["surah"]), str(b["ayah"]),
            b.get("note", ""),
            b.get("saved_at", "")[:16],
        )

    console.print()
    console.print(table)
    console.print(f"  [dim]quran bookmark goto <label>[/dim]\n")


@app.command("delete")
def delete_bookmark(label: Annotated[str, typer.Argument()]):
    """Delete a bookmark."""
    from quran.core.bookmark_store import delete_bookmark as _del

    if _del(label):
        console.print(f"[green]✓[/green] Deleted '{label}'.")
    else:
        console.print(f"[red]✗[/red] No bookmark named '{label}'.")
