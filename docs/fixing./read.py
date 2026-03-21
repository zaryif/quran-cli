"""
quran read — read any surah or ayah with Arabic + translation.

FIX v1.2.0:
  - Clear error message when fetch returns empty (first-run API miss,
    rather than silent blank output).
  - Added --dual2 flag: shows primary lang + secondary lang (lang2 from config)
    side by side, for users who configured two languages.
  - Language setting from config is properly applied.

Usage:
  quran read 1                      # Al-Fatihah by number
  quran read kahf                   # Surah Al-Kahf by name
  quran read "ya-sin"               # Surah Ya-Sin
  quran read 2:255                  # Ayat ul-Kursi
  quran read 2:1-10                 # range
  quran read 36 --lang bn           # Bangla
  quran read 18 --dual              # Arabic + primary translation
  quran read 18 --dual2             # primary lang + secondary lang (lang2)
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
        help="Language code: en, bn, ar, ur, tr, fr, id, ru, de, es, zh, nl, ms")] = "",
    dual:         Annotated[bool, typer.Option("--dual","-d",
        help="Arabic + primary translation side by side")] = False,
    dual2:        Annotated[bool, typer.Option("--dual2",
        help="Primary translation + secondary (lang2) side by side")] = False,
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
        console.print("  [dim]By number:    [/dim][green]quran read 1[/green]")
        console.print("  [dim]By name:      [/dim][green]quran read kahf[/green]")
        console.print("  [dim]Single ayah:  [/dim][green]quran read 2:255[/green]")
        console.print("  [dim]Range:        [/dim][green]quran read 2:1-10[/green]")
        console.print("  [dim]Bangla:       [/dim][green]quran read 18 --lang bn[/green]")
        console.print("  [dim]Dual (ar+tr): [/dim][green]quran read 36 --dual[/green]")
        console.print("  [dim]Two langs:    [/dim][green]quran read 36 --dual2[/green]")
        console.print()
        return

    from quran.config.settings import load
    from quran.core.quran_engine import (
        resolve_surah, get_surah_meta, fetch_surah, fetch_surah_dual,
        fetch_ayah_with_arabic, format_arabic, LANG_EDITIONS,
    )

    cfg   = load()
    lang  = lang or cfg.get("lang", "en")
    lang2 = cfg.get("lang2", "bn")

    # Validate language
    if lang not in LANG_EDITIONS:
        console.print(
            f"[red]✗[/red] Unknown language '[bold]{lang}[/bold]'.\n"
            f"  Supported: {', '.join(LANG_EDITIONS.keys())}\n"
            f"  Set default: [green]quran config set lang bn[/green]"
        )
        return

    # Resolve surah reference
    try:
        raw_surah, ayah_from, ayah_to = _parse_ref(ref)
    except ValueError:
        console.print(f"[red]✗[/red] Could not parse: [bold]{ref}[/bold]")
        return

    if isinstance(raw_surah, str):
        surah_n = resolve_surah(raw_surah)
        if not surah_n:
            console.print(f"[red]✗[/red] Surah not found: [bold]{raw_surah}[/bold]")
            console.print("[dim]Run [green]quran info surahs[/green] to see all 114 surahs.[/dim]")
            return
    else:
        surah_n = raw_surah

    meta = get_surah_meta(surah_n)
    if not meta:
        console.print(f"[red]✗[/red] Surah {surah_n} not found (valid: 1–114).")
        return

    _render_surah_header(meta)

    show_arabic = not no_arabic
    use_dual    = dual or arabic_only

    # ── Single ayah ───────────────────────────────────────────────────────────
    if ayah_from and ayah_from == ayah_to:
        with console.status(f"[dim]Fetching {meta['name']} {surah_n}:{ayah_from}…[/dim]"):
            ayah = fetch_ayah_with_arabic(surah_n, ayah_from, "en" if arabic_only else lang)
        if not ayah.get("arabic") and not ayah.get("text"):
            _fetch_error(meta["name"], surah_n, lang)
            return
        _render_ayah(ayah, surah_n, show_arabic=show_arabic,
                     lang_label=lang, arabic_only=arabic_only)
        return

    from_a = ayah_from or 1
    to_a   = ayah_to

    # ── dual2: primary lang + secondary lang ──────────────────────────────────
    if dual2:
        with console.status(
            f"[dim]Fetching {meta['name']} ({lang} + {lang2})…[/dim]"
        ):
            ayahs_p = fetch_surah(surah_n, lang, from_a, to_a)
            ayahs_s = fetch_surah(surah_n, lang2, from_a, to_a)

        if not ayahs_p:
            _fetch_error(meta["name"], surah_n, lang)
            return

        s_map = {a["ayah"]: a["text"] for a in ayahs_s}
        from quran.commands.lang import LANGUAGES
        l1_name = LANGUAGES.get(lang,  {}).get("native", lang)
        l2_name = LANGUAGES.get(lang2, {}).get("native", lang2)
        console.print(f"  [dim]{l1_name}[/dim]  ·  [dim]{l2_name}[/dim]\n")

        for a in ayahs_p:
            ref_s = f"[dim green]{surah_n}:{a['ayah']}[/dim green]"
            t2    = s_map.get(a["ayah"], "")
            console.print(f"  {ref_s}  [white]{a['text']}[/white]")
            if t2:
                console.print(f"        [dim]{t2}[/dim]")
            console.print()

        console.print(
            f"[dim]  ─── {meta['name']} · {len(ayahs_p)} ayahs · "
            f"{lang} + {lang2} ───[/dim]\n"
        )
        _auto_streak(len(ayahs_p))
        return

    # ── Arabic + primary translation (--dual) ─────────────────────────────────
    if use_dual:
        with console.status(
            f"[dim]Fetching {meta['name']} (dual: ar + {lang if not arabic_only else 'ar only'})…[/dim]"
        ):
            ayahs = fetch_surah_dual(surah_n, "en" if arabic_only else lang, from_a, to_a)

        if not ayahs:
            _fetch_error(meta["name"], surah_n, lang)
            return

        for ayah in ayahs:
            _render_ayah(ayah, surah_n, show_arabic=show_arabic,
                         lang_label=lang, arabic_only=arabic_only)

        console.print(
            f"[dim]  ─── {meta['name']} · {len(ayahs)} ayahs · "
            f"{'ar' if arabic_only else meta['type']} ───[/dim]\n"
        )
        _auto_streak(len(ayahs))
        return

    # ── Single language (default) ─────────────────────────────────────────────
    with console.status(
        f"[dim]Fetching {meta['name']} ({lang})…[/dim]"
    ):
        ayahs = fetch_surah(surah_n, lang, from_a, to_a)

    if not ayahs:
        _fetch_error(meta["name"], surah_n, lang)
        return

    for ayah in ayahs:
        ref_s = f"[dim green]{surah_n}:{ayah['ayah']}[/dim green]"
        console.print(f"  {ref_s}  {ayah['text']}")
        console.print()

    console.print(
        f"[dim]  ─── {meta['name']} · {len(ayahs)} ayahs · {meta['type']} ───[/dim]\n"
    )
    _auto_streak(len(ayahs))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_error(name: str, surah_n: int, lang: str) -> None:
    """
    Clear error when fetch returns empty — instead of the old silent blank screen.
    Tells the user exactly what happened and how to fix it.
    """
    console.print()
    console.print(
        f"  [red]✗[/red] Could not load [bold]{name}[/bold] in [bold]{lang}[/bold].\n"
    )
    console.print("  [dim]Possible reasons:[/dim]")
    console.print("  [yellow]·[/yellow] No internet on first run — quran-cli needs to fetch from AlQuran.cloud once")
    console.print("  [yellow]·[/yellow] API timeout — try again in a moment")
    console.print("  [yellow]·[/yellow] Unknown language code\n")
    console.print("  [dim]Try:[/dim]")
    console.print(f"  [green]quran read {surah_n} --lang en[/green]       [dim]← English always caches first[/dim]")
    console.print(f"  [green]quran config set lang {lang}[/green]    [dim]← verify language is set[/dim]")
    console.print(f"  [green]quran config show[/green]               [dim]← check all settings[/dim]")
    console.print()


def _auto_streak(count: int) -> None:
    """Auto-mark reading streak after successful read."""
    try:
        from quran.core.streak import mark_read
        mark_read(count)
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
