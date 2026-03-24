"""
quran read — read any surah or ayah with Arabic + translation.

FIX v1.2.7:
  - _interactive_read: fixed broken search call. The previous code imported
    and called search_cmd(query) directly, which fails because Typer command
    callbacks require a Context object as the first argument. Fixed by using
    subprocess.run (same pattern as gui.py _run) to dispatch the command.

Usage:
  quran read 1                      # Al-Fatihah by number
  quran read kahf                   # Surah Al-Kahf by name
  quran read "ya-sin"               # Surah Ya-Sin
  quran read 2:255                  # Ayat ul-Kursi
  quran read 2:1-10                 # range
  quran read 36 --lang bn           # Bangla
  quran read 18 --dual              # Arabic + primary translation
  quran read 18 --dual2             # primary lang + secondary lang (lang2)
  quran read 18 --dual --lang ur    # Arabic + Urdu (on the fly)
  quran read 18 --dual2 --lang en --lang2 bn # English + Bangla (on the fly)
  quran read --arabic-only 1        # Arabic text only
"""
from __future__ import annotations
import re
import typer
from rich.console import Console
from rich.rule import Rule
from rich.text import Text
from rich.align import Align
from typing import Optional, List, Dict
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
    lang2_opt:    Annotated[str,  typer.Option("--lang2", "--second",
        help="Secondary language code for dual2 mode")] = "",
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
        # Trigger interactive mode
        _interactive_read()
        return

    from quran.config.settings import load
    from quran.core.quran_engine import (
        resolve_surah, get_surah_meta, fetch_surah, fetch_surah_dual,
        fetch_ayah_with_arabic, format_arabic, LANG_EDITIONS,
    )

    cfg   = load()
    lang  = lang or cfg.get("lang", "en")
    lang2 = lang2_opt or cfg.get("lang2", "bn")

    # Auto-enable dual2 if lang2_opt was provided
    if lang2_opt and not dual:
        dual2 = True

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
    """Clear error when fetch returns empty."""
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

def _interactive_read():
    """Interactive navigation for reading the Quran."""
    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        console.print("[red]Error:[/red] [bold]simple-term-menu[/bold] is required for interactive mode.")
        console.print("       Install it with: [green]pip install simple-term-menu[/green]")
        return

    from quran.core.quran_engine import SURAH_META, LANG_EDITIONS
    from quran.config.settings import load
    from quran.commands.lang import LANGUAGES

    cfg = load()

    # 1. Main Action Menu
    actions = [
        "  Read Quran with Translation (Full Surah)",
        "  Interactive Ayah-by-Ayah (n/p/s)",
        "  Dual Mode (Arabic + Primary)",
        "  Dual Translation (Two Languages)",
        "  Search Quran",
        "  Exit"
    ]

    console.print()
    console.print(Rule("[bold green]Quran Navigator[/bold green]", style="green"))
    console.print()

    menu = TerminalMenu(
        actions,
        title="  Select an action:",
        menu_cursor_style=("fg_green", "bold"),
        menu_highlight_style=("fg_green", "bold"),
    )
    idx = menu.show()

    if idx is None or idx == 5:
        console.print("  [dim]Cancelled.[/dim]\n")
        return

    # 2. Surah Selection
    surah_labels = [f"{s[0]:3d}. {s[1]:20s} {s[2]}" for s in SURAH_META]
    surah_menu = TerminalMenu(
        surah_labels,
        title="  Select a Surah:",
        show_search_hint=True,
        menu_cursor_style=("fg_green", "bold"),
    )
    s_idx = surah_menu.show()
    if s_idx is None:
        return
    surah_n = SURAH_META[s_idx][0]

    # 3. Language Selection Helper
    def pick_lang(title: str) -> Optional[str]:
        lang_items = list(LANG_EDITIONS.keys())
        lang_labels = []
        for code in lang_items:
            name = LANGUAGES.get(code, {}).get("native", code)
            lang_labels.append(f"{code:4s}  {name}")
        l_menu = TerminalMenu(
            lang_labels,
            title=f"  {title}:",
            menu_cursor_style=("fg_green", "bold"),
        )
        l_idx = l_menu.show()
        return lang_items[l_idx] if l_idx is not None else None

    if idx == 0:  # Single Translation
        l1 = pick_lang("Select Translation Language")
        if not l1:
            return
        _run_read_logic(surah_n, lang=l1)

    elif idx == 1:  # Interactive Ayah-by-Ayah
        l1 = pick_lang("Select Translation Language")
        if not l1:
            return
        _read_ayah_by_ayah_flow(surah_n, lang=l1)

    elif idx == 2:  # Dual Mode (Arabic + L1)
        l1 = pick_lang("Select Translation Language")
        if not l1:
            return
        _run_read_logic(surah_n, lang=l1, dual=True)

    elif idx == 3:  # Dual Translation (L1 + L2)
        l1 = pick_lang("Select First Language")
        if not l1:
            return
        l2 = pick_lang("Select Second Language")
        if not l2:
            return
        _run_read_logic(surah_n, lang=l1, lang2_opt=l2, dual2=True)

    elif idx == 4:  # Search — BUG FIX: use subprocess, not direct function call
        console.print()
        console.print("  [dim]Enter a search keyword:[/dim]")
        console.print("  > ", end="")
        try:
            query = input().strip()
        except (KeyboardInterrupt, EOFError):
            return
        if query:
            import subprocess
            subprocess.run(f'quran search "{query}"', shell=True)


def _read_ayah_by_ayah_flow(surah_n: int, lang: str):
    """Interactive loop to read ayah by ayah using keys."""
    from quran.core.quran_engine import fetch_surah, get_surah_meta
    from simple_term_menu import TerminalMenu
    from quran.core.bookmark_store import save_bookmark

    meta = get_surah_meta(surah_n)
    if not meta:
        return

    console.print()
    console.print(f"[dim]Fetching {meta['name']}…[/dim]")
    ayahs = fetch_surah(surah_n, lang, 1, None)
    if not ayahs:
        _fetch_error(meta["name"], surah_n, lang)
        return

    _render_surah_header(meta)

    total = len(ayahs)
    current_idx = 0

    while True:
        a = ayahs[current_idx]
        console.clear()
        _render_surah_header(meta)

        # Print current Ayah
        console.print(f"  [dim green]{surah_n}:{a['ayah']}[/dim green]  {a['text']}\n")
        
        # Build prompt
        prompt = f"  [dim]Ayah {a['ayah']} of {total}  —  "
        if current_idx > 0:
            prompt += "(p) prev, "
        if current_idx < total - 1:
            prompt += "(n) next, "
        prompt += "(s) save bookmark, (q) quit[/dim]"

        console.print(prompt)

        menu = TerminalMenu(
            ["n", "p", "s", "q"],
            show_search_hint=False,
            menu_cursor_style=("fg_green", "bold"),
            clear_screen=False,
            # We don't actually want them to select from a menu, we just want a single keystroke.
            # But simple-term-menu accepts keystrokes directly. We'll use getch.
        )
        # Using simple_term_menu's underlying getch is tricky. We'll use Python's built-in input if we have to, 
        # or we just show a small 4-item menu:
        menu_items = []
        if current_idx < total - 1: menu_items.append("Next Ayah (Default)")
        if current_idx > 0: menu_items.append("Previous Ayah")
        menu_items.append("Save Bookmark")
        menu_items.append("Quit")

        nav_menu = TerminalMenu(
            menu_items,
            title="",
            menu_cursor_style=("fg_green", "bold")
        )
        choice_idx = nav_menu.show()
        if choice_idx is None:
            break
        
        choice_str = menu_items[choice_idx]

        if choice_str.startswith("Next"):
            current_idx += 1
        elif choice_str.startswith("Previous"):
            current_idx -= 1
        elif choice_str.startswith("Save"):
            console.print("\n  [dim]Enter a label to save this bookmark (e.g., 'morning_read'):[/dim]")
            console.print("  > ", end="")
            try:
                label = input().strip()
                if label:
                    save_bookmark(label, b_type="quran", surah=surah_n, ayah=a["ayah"])
                    console.print(f"\n  [green]✓ Saved bookmark: '{label}'[/green]")
                    import time
                    time.sleep(1)
            except (KeyboardInterrupt, EOFError):
                pass
        elif choice_str.startswith("Quit"):
            break

    console.print("\n  [dim]Exited Interactive Reading.[/dim]\n")



def _run_read_logic(surah_n: int, lang: str = "", lang2_opt: str = "",
                   dual: bool = False, dual2: bool = False,
                   arabic_only: bool = False, no_arabic: bool = False):
    """Internal logic extracted from read_cmd for use by _interactive_read."""
    from quran.config.settings import load
    from quran.core.quran_engine import (
        get_surah_meta, fetch_surah, fetch_surah_dual,
        fetch_ayah_with_arabic, LANG_EDITIONS,
    )

    cfg   = load()
    lang  = lang or cfg.get("lang", "en")
    lang2 = lang2_opt or cfg.get("lang2", "bn")

    if lang2_opt and not dual:
        dual2 = True

    meta = get_surah_meta(surah_n)
    if not meta:
        return

    _render_surah_header(meta)

    show_arabic = not no_arabic
    use_dual    = dual or arabic_only

    from_a = 1
    to_a   = None

    if dual2:
        with console.status(f"[dim]Fetching {meta['name']} ({lang} + {lang2})…[/dim]"):
            ayahs_p = fetch_surah(surah_n, lang, from_a, to_a)
            ayahs_s = fetch_surah(surah_n, lang2, from_a, to_a)
        if not ayahs_p:
            _fetch_error(meta["name"], surah_n, lang)
            return
        s_map = {a["ayah"]: a["text"] for a in ayahs_s}
        for a in ayahs_p:
            ref_s = f"[dim green]{surah_n}:{a['ayah']}[/dim green]"
            t2    = s_map.get(a["ayah"], "")
            console.print(f"  {ref_s}  [white]{a['text']}[/white]")
            if t2:
                console.print(f"        [dim]{t2}[/dim]")
            console.print()
        return

    if use_dual:
        with console.status(f"[dim]Fetching {meta['name']} (ar + {lang})…[/dim]"):
            ayahs = fetch_surah_dual(surah_n, lang, from_a, to_a)
        if not ayahs:
            _fetch_error(meta["name"], surah_n, lang)
            return
        for ayah in ayahs:
            _render_ayah(ayah, surah_n, show_arabic=show_arabic,
                         lang_label=lang, arabic_only=arabic_only)
        return

    with console.status(f"[dim]Fetching {meta['name']} ({lang})…[/dim]"):
        ayahs = fetch_surah(surah_n, lang, from_a, to_a)
    if not ayahs:
        _fetch_error(meta["name"], surah_n, lang)
        return
    for ayah in ayahs:
        ref_s = f"[dim green]{surah_n}:{ayah['ayah']}[/dim green]"
        console.print(f"  {ref_s}  {ayah['text']}")
        console.print()
