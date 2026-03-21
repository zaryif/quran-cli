"""quote.py — daily ayah display"""
from __future__ import annotations
from rich.console import Console
from rich.panel import Panel

console = Console()


def show_quote() -> None:
    from quran.config.settings import load
    from quran.core.quran_engine import get_daily_ayah, get_surah_meta

    cfg  = load()
    lang = cfg.get("lang", "en")
    ayah = get_daily_ayah(lang)

    if not ayah:
        console.print("[dim]Could not load daily ayah. Check your connection.[/dim]")
        return

    meta = ayah.get("meta") or {}
    ref  = f"{meta.get('name','?')}  {ayah['surah']}:{ayah['ayah']}"

    console.print()
    console.print(
        Panel(
            f"[white]{ayah['text']}[/white]\n\n[dim green]{ref}[/dim green]",
            title="[dim]daily ayah[/dim]",
            border_style="green",
            padding=(1, 3),
        )
    )
    console.print()
