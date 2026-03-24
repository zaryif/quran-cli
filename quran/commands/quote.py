"""quote.py — daily ayah display"""
from __future__ import annotations
from rich.console import Console
from rich.panel import Panel

console = Console()


def show_quote() -> None:
    from quran.config.settings import load
    from quran.core.quran_engine import get_random_ayah, get_surah_meta

    cfg  = load()
    lang = cfg.get("lang", "en")
    ayah = get_random_ayah(lang)

    if not ayah:
        console.print("  [red]✗[/red] Failed to fetch random ayah. Check your connection.")
        return

    meta = get_surah_meta(ayah["surah"])
    ref  = f"{meta['name']} {ayah['surah']}:{ayah['ayah']}"

    console.print()
    console.print(
        Panel(
            f"[white]{ayah['text']}[/white]\n\n[dim green]{ref}[/dim green]",
            title="[dim]random ayah[/dim]",
            border_style="green",
            padding=(1, 3),
        )
    )
    console.print()
    
    console.print("  [dim]Press 's' to save a bookmark, or any other key to exit.[/dim]")
    try:
        console.print("  > ", end="")
        key = input().strip().lower()
        if key == "s":
            console.print("  [dim]Enter a name for this bookmark:[/dim]")
            console.print("  > ", end="")
            label = input().strip()
            if label:
                from quran.core.bookmark_store import save_bookmark
                save_bookmark(label, b_type="quran", surah=ayah["surah"], ayah=ayah["ayah"])
                console.print(f"  [green]✓ Saved bookmark: '{label}'[/green]\n")
                import time; time.sleep(0.5)
    except (KeyboardInterrupt, EOFError):
        pass

