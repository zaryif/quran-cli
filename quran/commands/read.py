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
    size:         Annotated[str,  typer.Option("--size", "-s",
        help="Text display size: small, medium, large")] = "medium",
    mode:         Annotated[str,  typer.Option("--mode", "-m",
        help="Reading mode: full (all at once), ayah (one-by-one), page (5 per page)")] = "full",
):
    if ctx.invoked_subcommand:
        return

    # Validate size/mode
    size = size.lower()
    mode = mode.lower()
    if size not in ("small", "medium", "large"):
        console.print(f"[red]✗[/red] Invalid size '{size}'. Use: small, medium, large")
        return
    if mode not in ("full", "ayah", "page"):
        console.print(f"[red]✗[/red] Invalid mode '{mode}'. Use: full, ayah, page")
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
        _render_ayah_sized(ayah, surah_n, size=size, show_arabic=show_arabic,
                          arabic_only=arabic_only)
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

        # Inject second-language text into ayahs for unified rendering
        for a in ayahs_p:
            a["text2"] = s_map.get(a["ayah"], "")

        _dispatch_mode(ayahs_p, surah_n, meta, mode, size, show_arabic=True,
                       arabic_only=False, dual2_mode=True)
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

        _dispatch_mode(ayahs, surah_n, meta, mode, size, show_arabic=show_arabic,
                       arabic_only=arabic_only)
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

    _dispatch_mode(ayahs, surah_n, meta, mode, size, show_arabic=show_arabic,
                   arabic_only=arabic_only)
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
    """Legacy renderer — delegates to sized version with medium."""
    _render_ayah_sized(ayah, surah_n, size="medium", show_arabic=show_arabic,
                       arabic_only=arabic_only)


def _render_ayah_sized(ayah: dict, surah_n: int, *, size: str = "medium",
                       show_arabic: bool = True, arabic_only: bool = False,
                       dual2_mode: bool = False) -> None:
    """Render a single ayah with size-aware formatting.

    Sizes:
      small  — compact: ref + text on one line, no Arabic, no spacing
      medium — current default: Arabic right-aligned + translation + 1 blank line
      large  — panel-wrapped: Arabic header, padded translation, horizontal rule
    """
    from rich.panel import Panel
    from quran.core.quran_engine import format_arabic

    ref_s = f"[dim green]{surah_n}:{ayah['ayah']}[/dim green]"

    if size == "small":
        # ── Small: compact single line ────────────────────────────────────
        if arabic_only and ayah.get("arabic"):
            ar = format_arabic(ayah["arabic"])
            console.print(f"  {ref_s}  [yellow]{ar}[/yellow]")
        elif ayah.get("text"):
            console.print(f"  {ref_s}  [dim]{ayah['text']}[/dim]")
        if dual2_mode and ayah.get("text2"):
            console.print(f"         [dim italic]{ayah['text2']}[/dim italic]")

    elif size == "large":
        # ── Large: panel-wrapped with padding ─────────────────────────────
        body_parts = []

        if show_arabic and ayah.get("arabic") and not arabic_only:
            ar_display = format_arabic(ayah["arabic"])
            body_parts.append(f"[bold yellow]{ar_display}[/bold yellow]")
            body_parts.append("")

        if not arabic_only and ayah.get("text"):
            body_parts.append(f"  {ayah['text']}")

        if arabic_only and ayah.get("arabic"):
            ar_display = format_arabic(ayah["arabic"])
            body_parts.append(f"[bold yellow]{ar_display}[/bold yellow]")

        if dual2_mode and ayah.get("text2"):
            body_parts.append(f"  [dim]{ayah['text2']}[/dim]")

        panel_text = "\n".join(body_parts) if body_parts else ""
        console.print(Panel(
            panel_text,
            title=f"[green]{surah_n}:{ayah['ayah']}[/green]",
            border_style="bright_black",
            padding=(1, 3),
        ))
        console.print()

    else:
        # ── Medium: current default behavior ──────────────────────────────
        if show_arabic and ayah.get("arabic"):
            ar_display = format_arabic(ayah["arabic"])
            console.print(Align.right(
                Text(ar_display, style="bold yellow", justify="right"),
                width=console.width - 4
            ))

        if not arabic_only and ayah.get("text"):
            console.print(f"  {ref_s}  {ayah['text']}")

        if dual2_mode and ayah.get("text2"):
            console.print(f"        [dim]{ayah['text2']}[/dim]")

        console.print()


# ── Mode dispatcher ──────────────────────────────────────────────────────────

PAGE_SIZE = 5


def _dispatch_mode(ayahs: list, surah_n: int, meta: dict, mode: str, size: str,
                   show_arabic: bool = True, arabic_only: bool = False,
                   dual2_mode: bool = False) -> None:
    """Route rendering to the appropriate mode: full, ayah, or page."""
    if mode == "ayah":
        _ayah_by_ayah_cli(ayahs, surah_n, meta, size, show_arabic=show_arabic,
                          arabic_only=arabic_only, dual2_mode=dual2_mode)
    elif mode == "page":
        _paged_read(ayahs, surah_n, meta, size, show_arabic=show_arabic,
                    arabic_only=arabic_only, dual2_mode=dual2_mode)
    else:
        # full — render all at once
        for ayah in ayahs:
            _render_ayah_sized(ayah, surah_n, size=size, show_arabic=show_arabic,
                               arabic_only=arabic_only, dual2_mode=dual2_mode)
        console.print(
            f"[dim]  ─── {meta['name']} · {len(ayahs)} ayahs ───[/dim]\n"
        )


def _paged_read(ayahs: list, surah_n: int, meta: dict, size: str, *,
                show_arabic: bool = True, arabic_only: bool = False,
                dual2_mode: bool = False) -> None:
    """Read ayahs in pages of PAGE_SIZE with navigation."""
    total    = len(ayahs)
    pages    = (total + PAGE_SIZE - 1) // PAGE_SIZE
    cur_page = 0

    while True:
        start = cur_page * PAGE_SIZE
        end   = min(start + PAGE_SIZE, total)
        chunk = ayahs[start:end]

        console.print()
        console.print(Rule(
            f"[dim]{meta['name']}  ·  Page {cur_page + 1} of {pages}  ·  "
            f"Ayahs {start + 1}–{end} of {total}[/dim]",
            style="bright_black"
        ))
        console.print()

        for ayah in chunk:
            _render_ayah_sized(ayah, surah_n, size=size, show_arabic=show_arabic,
                               arabic_only=arabic_only, dual2_mode=dual2_mode)

        # Navigation prompt
        nav_parts = []
        if cur_page < pages - 1:
            nav_parts.append("[green]Enter[/green]/[green]n[/green] next")
        if cur_page > 0:
            nav_parts.append("[green]p[/green] prev")
        nav_parts.append("[green]q[/green] quit")
        prompt = "  [dim]" + "  ·  ".join(nav_parts) + "[/dim]"
        console.print(prompt)
        console.print("  > ", end="")

        try:
            key = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if key in ("q", "quit", "exit"):
            break
        elif key in ("p", "prev", "b", "back"):
            if cur_page > 0:
                cur_page -= 1
        elif key in ("", "n", "next"):
            if cur_page < pages - 1:
                cur_page += 1
            else:
                break  # last page, Enter exits
        else:
            # Try interpreting as page number
            try:
                pg = int(key)
                if 1 <= pg <= pages:
                    cur_page = pg - 1
            except ValueError:
                pass

    console.print(f"\n[dim]  ─── {meta['name']} · {total} ayahs ───[/dim]\n")


def _ayah_by_ayah_cli(ayahs: list, surah_n: int, meta: dict, size: str, *,
                      show_arabic: bool = True, arabic_only: bool = False,
                      dual2_mode: bool = False) -> None:
    """Read one ayah at a time with n/p/q navigation (CLI flag version)."""
    total = len(ayahs)
    idx   = 0

    while True:
        ayah = ayahs[idx]
        console.print()
        console.print(Rule(
            f"[dim]{meta['name']}  ·  Ayah {idx + 1} of {total}[/dim]",
            style="bright_black"
        ))
        console.print()
        _render_ayah_sized(ayah, surah_n, size=size, show_arabic=show_arabic,
                           arabic_only=arabic_only, dual2_mode=dual2_mode)

        # Navigation
        nav = []
        if idx < total - 1:
            nav.append("[green]Enter[/green]/[green]n[/green] next")
        if idx > 0:
            nav.append("[green]p[/green] prev")
        nav.append("[green]s[/green] bookmark")
        nav.append("[green]q[/green] quit")
        console.print("  [dim]" + "  ·  ".join(nav) + "[/dim]")
        console.print("  > ", end="")

        try:
            key = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if key in ("q", "quit"):
            break
        elif key in ("p", "prev"):
            if idx > 0:
                idx -= 1
        elif key in ("s", "save"):
            _save_bookmark_prompt(surah_n, ayah["ayah"])
        elif key in ("", "n", "next"):
            if idx < total - 1:
                idx += 1
            else:
                break
        else:
            # Try jumping to ayah number
            try:
                target = int(key)
                for i, a in enumerate(ayahs):
                    if a["ayah"] == target:
                        idx = i
                        break
            except ValueError:
                pass

    console.print(f"\n[dim]  ─── {meta['name']} · {total} ayahs ───[/dim]\n")


def _save_bookmark_prompt(surah_n: int, ayah_num: int) -> None:
    """Prompt to save a bookmark at the current position."""
    from quran.core.bookmark_store import save_bookmark
    console.print("\n  [dim]Enter bookmark label (e.g. 'morning_read'):[/dim]")
    console.print("  > ", end="")
    try:
        label = input().strip()
        if label:
            save_bookmark(label, b_type="quran", surah=surah_n, ayah=ayah_num)
            console.print(f"  [green]✓ Bookmark saved: '{label}'[/green]")
    except (KeyboardInterrupt, EOFError):
        pass



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
        "  Read Full Surah",
        "  Read Page-by-Page (5 ayahs)",
        "  Read Ayah-by-Ayah",
        "  Dual Mode (Arabic + Translation)",
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

    if idx is None or idx == len(actions) - 1:
        console.print("  [dim]Cancelled.[/dim]\n")
        return

    # Search shortcut — doesn't need surah/lang/size pickers
    if idx == 5:
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

    # 4. Text Size Picker
    def pick_size() -> str:
        size_options = [
            "  Small   — compact, no Arabic, minimal spacing",
            "  Medium  — Arabic + translation (default)",
            "  Large   — panel-wrapped, extra padding, prominent",
        ]
        s_menu = TerminalMenu(
            size_options,
            title="  Text size:",
            menu_cursor_style=("fg_green", "bold"),
            cursor_index=1,  # default to medium
        )
        s_idx = s_menu.show()
        return ["small", "medium", "large"][s_idx] if s_idx is not None else "medium"

    # Map action index → reading mode
    mode_map = {0: "full", 1: "page", 2: "ayah", 3: "full", 4: "full"}
    mode = mode_map.get(idx, "full")

    if idx in (0, 1, 2):  # Single translation modes
        l1 = pick_lang("Select Translation Language")
        if not l1:
            return
        sz = pick_size()
        _run_read_logic(surah_n, lang=l1, size=sz, mode=mode)

    elif idx == 3:  # Dual Mode (Arabic + L1)
        l1 = pick_lang("Select Translation Language")
        if not l1:
            return
        sz = pick_size()
        _run_read_logic(surah_n, lang=l1, dual=True, size=sz, mode=mode)

    elif idx == 4:  # Dual Translation (L1 + L2)
        l1 = pick_lang("Select First Language")
        if not l1:
            return
        l2 = pick_lang("Select Second Language")
        if not l2:
            return
        sz = pick_size()
        _run_read_logic(surah_n, lang=l1, lang2_opt=l2, dual2=True, size=sz, mode=mode)


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
                   arabic_only: bool = False, no_arabic: bool = False,
                   size: str = "medium", mode: str = "full"):
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
            a["text2"] = s_map.get(a["ayah"], "")
        _dispatch_mode(ayahs_p, surah_n, meta, mode, size, show_arabic=True,
                       arabic_only=False, dual2_mode=True)
        return

    if use_dual:
        with console.status(f"[dim]Fetching {meta['name']} (ar + {lang})…[/dim]"):
            ayahs = fetch_surah_dual(surah_n, lang, from_a, to_a)
        if not ayahs:
            _fetch_error(meta["name"], surah_n, lang)
            return
        _dispatch_mode(ayahs, surah_n, meta, mode, size, show_arabic=show_arabic,
                       arabic_only=arabic_only)
        return

    with console.status(f"[dim]Fetching {meta['name']} ({lang})…[/dim]"):
        ayahs = fetch_surah(surah_n, lang, from_a, to_a)
    if not ayahs:
        _fetch_error(meta["name"], surah_n, lang)
        return
    _dispatch_mode(ayahs, surah_n, meta, mode, size, show_arabic=show_arabic,
                   arabic_only=arabic_only)

