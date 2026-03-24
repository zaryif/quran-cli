"""
quran bookmark — save and navigate reading positions for Quran and Hadith.
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich import box
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Save and navigate bookmarks (Quran and Hadith).")
console = Console()


@app.callback(invoke_without_command=True)
def bookmark_cmd(ctx: typer.Context):
    """View and manage your saved bookmarks interactively."""
    if ctx.invoked_subcommand is None:
        interactive_bookmarks()


def interactive_bookmarks():
    """Show an interactive menu to browse and jump to bookmarks."""
    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        console.print("[red]Error:[/red] [bold]simple-term-menu[/bold] is required for interactive bookmarks.")
        return

    from quran.core.bookmark_store import list_bookmarks
    bms = list_bookmarks()

    if not bms:
        console.print("[dim]No bookmarks yet.[/dim]")
        console.print("  [dim]Start reading the Quran or Hadith and press [green]s[/green] to save a bookmark![/dim]\n")
        return

    # Sort bookmarks by type and then saved_at
    sorted_bms = sorted(bms.items(), key=lambda x: (x[1].get("type", "quran"), x[1].get("saved_at", "")))

    labels = []
    keys_map = []
    for key, data in sorted_bms:
        b_type = data.get("type", "quran").capitalize()
        if b_type == "Quran":
            desc = f"Surah {data.get('surah')}:{data.get('ayah')}"
        elif b_type == "Hadith":
            desc = f"{data.get('collection', '').capitalize()} — Book {data.get('book')} Hadith {data.get('number')}"
        else:
            desc = "Unknown"
            
        note = f" - {data['note']}" if data.get("note") else ""
        labels.append(f"[{b_type}] {key} ({desc}){note}")
        keys_map.append(key)

    labels.append("[Exit]")

    console.print()
    console.print("  [bold green]Your Bookmarks[/bold green]")
    console.print()

    menu = TerminalMenu(
        labels,
        title="  Select a bookmark to jump to:",
        menu_cursor_style=("fg_green", "bold"),
    )
    idx = menu.show()

    if idx is None or idx == len(labels) - 1:
        console.print("  [dim]Cancelled.[/dim]\n")
        return

    selected_key = keys_map[idx]
    _goto_internal(selected_key)


def _goto_internal(label: str, lang: str = ""):
    """Internal logic to jump to a bookmark of any type."""
    from quran.core.bookmark_store import get_bookmark
    from quran.config.settings import load
    
    cfg  = load()
    lang = lang or cfg.get("lang", "en")
    bm   = get_bookmark(label)

    if not bm:
        console.print(f"[red]✗[/red] No bookmark named '{label}'.")
        return

    b_type = bm.get("type", "quran")

    if b_type == "quran":
        console.print(f"[dim]→ jumping to [bold]{label}[/bold] — Quran {bm['surah']}:{bm['ayah']}[/dim]\n")
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

    elif b_type == "hadith":
        col = bm.get("collection")
        book = bm.get("book")
        num = bm.get("number")
        
        console.print(f"[dim]→ jumping to [bold]{label}[/bold] — Hadith {col.capitalize()} Book {book} Hadith {num}[/dim]\n")
        import subprocess
        subprocess.run(f"quran hadith read {col} {book} {num}", shell=True)
    else:
        console.print(f"[red]✗[/red] Unknown bookmark type: {b_type}")


@app.command("save")
def save_bookmark(
    label: Annotated[str,           typer.Argument(help="Bookmark name e.g. 'fajr'")],
    ref:   Annotated[Optional[str], typer.Argument(help="Surah:ayah e.g. 18:1")] = None,
    note:  Annotated[str,           typer.Option("--note", "-n")] = "",
):
    """Save a Quran reading position manually."""
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

    _save(label, b_type="quran", surah=surah, ayah=ayah, note=note)
    console.print(f"[green]✓[/green] Saved '[bold]{label}[/bold]' → {surah}:{ayah}")


@app.command("goto")
def goto_bookmark(
    label: Annotated[str, typer.Argument(help="Bookmark name")],
    lang:  Annotated[str, typer.Option("--lang", "-l")] = "",
):
    """Jump to a saved bookmark."""
    _goto_internal(label, lang)


@app.command("list")
def list_bookmarks():
    """List all saved bookmarks as a table."""
    interactive_bookmarks()


@app.command("delete")
def delete_bookmark(label: Annotated[str, typer.Argument()]):
    """Delete a bookmark."""
    from quran.core.bookmark_store import delete_bookmark as _del

    if _del(label):
        console.print(f"[green]✓[/green] Deleted '{label}'.")
    else:
        console.print(f"[red]✗[/red] No bookmark named '{label}'.")
