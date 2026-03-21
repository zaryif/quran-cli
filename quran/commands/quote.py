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
