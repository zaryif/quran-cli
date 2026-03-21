"""
quran read — read any surah or ayah with Arabic + translation.

Usage:
  quran read 1                      # Al-Fatihah by number
  quran read kahf                   # Surah Al-Kahf by name
  quran read "ya-sin"               # Surah Ya-Sin
  quran read 2:255                  # Ayat ul-Kursi
  quran read 2:1-10                 # range
  quran read 36 --lang bn           # Bangla
  quran read 18 --dual              # Arabic + translation side by side
  quran read --arabic-only 1        # Arabic text only
"""
from __future__ import annotations
import re
import typer
from rich.console import Console
from rich.rule import Rule
from rich.text import Text
from rich.align import Align
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Read Quran by surah or ayah reference.")
console = Console()


def _parse_ref(ref: str) -> tuple[int | str, Optional[int], Optional[int]]:
    """Parse '2', 'kahf', '2:255', '2:1-10' → (surah_id, from, to)."""
    ref = ref.strip()
    if ":" in ref:
        s, a = ref.split(":", 1)
        surah_id: int | str = int(s) if s.isdigit() else s
        if "-" in a:
            a1, a2 = a.split("-", 1)
            return surah_id, int(a1), int(a2)
        return surah_id, int(a), int(a)
    return (int(ref) if ref.isdigit() else ref), None, None


@app.callback(invoke_without_command=True, context_settings={"allow_interspersed_args": True})
def read_cmd(
    ctx:          typer.Context,
    ref:          Annotated[Optional[str], typer.Argument(
        help="Surah number, name, or ayah ref: '1', 'kahf', '2:255', '18:1-10'")] = None,
    lang:         Annotated[str,  typer.Option("--lang","-l",
        help="Language: en, bn, ar, ur, tr, fr, id, ru, de, es")] = "",
    dual:         Annotated[bool, typer.Option("--dual","-d",
        help="Arabic + translation side by side")] = False,
    arabic_only:  Annotated[bool, typer.Option("--arabic-only",
        help="Show Arabic text only")] = False,
    no_arabic:    Annotated[bool, typer.Option("--no-arabic",
        help="Show translation only, no Arabic")] = False,
):
    if ctx.invoked_subcommand:
        return

    if ref is None:
        console.print()
        console.print("  [dim]Usage: quran read [bold]<surah>[/bold][/dim]")
        console.print()
        console.print("  [dim]By number:  [/dim][green]quran read 1[/green]")
        console.print("  [dim]By name:    [/dim][green]quran read kahf[/green]")
        console.print("  [dim]Single ayah:[/dim][green] quran read 2:255[/green]")
        console.print("  [dim]Range:      [/dim][green]quran read 2:1-10[/green]")
        console.print("  [dim]Bangla:     [/dim][green]quran read 18 --lang bn[/green]")
        console.print("  [dim]Dual:       [/dim][green]quran read 36 --dual[/green]")
        console.print()
        return

    from quran.config.settings import load
    from quran.core.quran_engine import (
        resolve_surah, get_surah_meta, fetch_surah, fetch_surah_dual,
        fetch_ayah_with_arabic, format_arabic, LANG_EDITIONS,
    )

    cfg  = load()
    lang = lang or cfg.get("lang", "en")

    # Validate language
    if lang not in LANG_EDITIONS:
        console.print(f"[red]✗[/red] Unknown language '{lang}'. "
                      f"Supported: {', '.join(LANG_EDITIONS.keys())}")
        return

    # Resolve surah reference
    try:
        raw_surah, ayah_from, ayah_to = _parse_ref(ref)
    except ValueError:
        console.print(f"[red]✗[/red] Could not parse: [bold]{ref}[/bold]")
        return

    # Resolve by name if string
    if isinstance(raw_surah, str):
        surah_n = resolve_surah(raw_surah)
        if not surah_n:
            console.print(f"[red]✗[/red] Surah not found: [bold]{raw_surah}[/bold]")
            console.print("[dim]Try: quran info surahs — to see all 114 surahs[/dim]")
            return
    else:
        surah_n = raw_surah

    meta = get_surah_meta(surah_n)
    if not meta:
        console.print(f"[red]✗[/red] Surah {surah_n} not found (valid: 1–114).")
        return

    # Print header
    _render_surah_header(meta)

    show_arabic = not no_arabic
    use_dual    = dual or arabic_only

    # Single ayah
    if ayah_from and ayah_from == ayah_to:
        with console.status(f"[dim]Fetching {meta['name']} {surah_n}:{ayah_from}…[/dim]"):
            ayah = fetch_ayah_with_arabic(surah_n, ayah_from, "en" if arabic_only else lang)
        if not ayah.get("arabic") and not ayah.get("text"):
            console.print(f"[red]✗[/red] Could not fetch {surah_n}:{ayah_from}. Check connection.")
            return
        _render_ayah(ayah, surah_n, show_arabic=show_arabic,
                     lang_label=lang, arabic_only=arabic_only)
        return

    # Full surah or range
    from_a = ayah_from or 1
    to_a   = ayah_to

    with console.status(f"[dim]Fetching {meta['name']} ({"dual" if use_dual else lang})…[/dim]"):
        if use_dual:
            ayahs = fetch_surah_dual(surah_n, "en" if arabic_only else lang, from_a, to_a)
        else:
            ayahs = fetch_surah(surah_n, lang, from_a, to_a)

    if not ayahs:
        console.print(f"[red]✗[/red] Could not fetch {meta['name']}. Check internet connection.")
        return

    for ayah in ayahs:
        if use_dual:
            _render_ayah(ayah, surah_n, show_arabic=show_arabic,
                         lang_label=lang, arabic_only=arabic_only)
        else:
            ref_s = f"[dim green]{surah_n}:{ayah['ayah']}[/dim green]"
            console.print(f"  {ref_s}  {ayah['text']}")
            console.print()

    console.print(f"[dim]  ─── {meta['name']} · {len(ayahs)} ayahs · {meta['type']} ───[/dim]\n")

    # Auto-mark reading streak
    try:
        from quran.core.streak import mark_read
        mark_read(len(ayahs))
    except Exception:
        pass


def _render_surah_header(meta: dict) -> None:
    console.print()
    console.print(Rule(
        f"[bold green]{meta['name']}[/bold green]  "
        f"[dim]{meta['meaning']}  ·  {meta['ayahs']} ayahs  ·  {meta['type']}[/dim]",
        style="green"
    ))
    console.print()


def _render_ayah(ayah: dict, surah_n: int,
                 show_arabic: bool, lang_label: str, arabic_only: bool) -> None:
    from quran.core.quran_engine import format_arabic

    ref_s = f"[dim green]{surah_n}:{ayah['ayah']}[/dim green]"

    if show_arabic and ayah.get("arabic"):
        ar_display = format_arabic(ayah["arabic"])
        console.print(Align.right(
            Text(ar_display, style="bold yellow", justify="right"),
            width=console.width - 4
        ))

    if not arabic_only and ayah.get("text"):
        console.print(f"  {ref_s}  {ayah['text']}")

    console.print()
