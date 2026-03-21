"""
quran cache — download Quran data for fully offline use.

Usage:
  quran cache                  # show what's currently cached
  quran cache download         # interactive: pick languages, download all 114 surahs
  quran cache download --all   # download every language (13 translations)
  quran cache clear            # delete the cache to free disk space
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, MofNCompleteColumn
from rich.rule import Rule
from rich.table import Table
from rich import box
from typing_extensions import Annotated

app     = typer.Typer(help="Download Quran for offline use.")
console = Console()


@app.callback(invoke_without_command=True)
def cache_cmd(ctx: typer.Context):
    """Show current cache status."""
    if ctx.invoked_subcommand:
        return
    _show_status()


@app.command("download")
def cache_download(
    all_langs: Annotated[bool, typer.Option(
        "--all", "-a", help="Download all 13 languages without prompting"
    )] = False,
    lang: Annotated[str, typer.Option(
        "--lang", "-l", help="Download a specific language (e.g. en, bn, ar)"
    )] = "",
):
    """Download all 114 surahs for offline reading."""
    from quran.core.quran_engine import LANG_EDITIONS, SURAH_META, _cache_surah
    from quran.config.settings import load

    cfg = load()

    # ── Explain ──────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold green]quran cache download[/bold green]\n\n"
        "[dim]This downloads all 114 surahs from AlQuran.cloud and stores them\n"
        "in a local SQLite database on your machine. After downloading,\n"
        "every [bold]quran read[/bold] command works fully offline — no internet needed.\n\n"
        "Already-cached surahs are skipped automatically (no re-download).\n"
        "Typical size: ~2–4 MB per language.[/dim]",
        border_style="green", padding=(1, 2),
    ))

    # ── Decide which languages ───────────────────────────────────────────────
    all_codes = list(LANG_EDITIONS.keys())

    if all_langs:
        selected = all_codes
    elif lang:
        if lang not in LANG_EDITIONS:
            console.print(f"[red]✗[/red] Unknown language '{lang}'. "
                          f"Available: {', '.join(all_codes)}")
            return
        selected = [lang]
    else:
        selected = _interactive_pick(all_codes, cfg)
        if not selected:
            console.print("\n  [dim]No languages selected. Nothing to download.[/dim]\n")
            return

    # ── Download ─────────────────────────────────────────────────────────────
    total = len(selected) * 114
    success = 0
    skipped = 0
    failed  = 0

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TextColumn("[dim]{task.fields[status]}[/dim]"),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading…", total=total, status="")

        for lang_code in selected:
            for surah_num, name, meaning, ayahs, typ in SURAH_META:
                progress.update(task,
                    description=f"[green]{lang_code}[/green] {name}",
                    status=f"{surah_num}/114")
                try:
                    cached = _cache_surah(surah_num, lang_code)
                    if cached:
                        success += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
                progress.advance(task)

    # ── Summary ──────────────────────────────────────────────────────────────
    console.print()
    _show_status()

    if failed:
        console.print(f"  [yellow]⚠[/yellow]  {failed} surahs could not be fetched "
                      f"(network issue). Re-run to retry.\n")
    else:
        console.print(f"  [green]✓[/green]  All done! [bold]quran read[/bold] now works "
                      f"fully offline for: [green]{', '.join(selected)}[/green]\n")


@app.command("clear")
def cache_clear():
    """Delete the local cache to free disk space."""
    from quran.core.quran_engine import DB_PATH

    if not DB_PATH.exists():
        console.print("[dim]No cache to clear.[/dim]")
        return

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)

    console.print(f"\n  [yellow]⚠[/yellow]  This will delete {size_mb:.1f} MB of cached Quran data.")
    console.print("  Next time you read, surahs will be re-fetched from the internet.\n")
    console.print("[dim]Delete cache? (y/N):[/dim] ", end="")

    try:
        choice = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        console.print("\n[dim]Cancelled.[/dim]")
        return

    if choice in ("y", "yes"):
        DB_PATH.unlink()
        console.print("[green]✓[/green] Cache deleted.")
    else:
        console.print("[dim]Cancelled.[/dim]")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _show_status():
    """Display what's currently in the cache."""
    from quran.core.quran_engine import cache_status, LANG_EDITIONS, DB_PATH

    LANG_NAMES = {
        "en": "English",   "bn": "Bangla",    "ar": "Arabic",
        "ur": "Urdu",      "tr": "Turkish",   "fr": "French",
        "id": "Indonesian", "ru": "Russian",   "de": "German",
        "es": "Spanish",   "zh": "Chinese",   "nl": "Dutch",
        "ms": "Malay",
    }

    stats = cache_status()

    console.print()
    console.print(Rule("[dim]quran cache status[/dim]", style="green"))
    console.print()

    if not stats["languages"]:
        console.print("  [dim]No surahs cached yet.[/dim]")
        console.print(f"  [dim]Run [green]quran cache download[/green] to go offline.[/dim]\n")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim",
                  border_style="bright_black", padding=(0, 2))
    table.add_column("Language", width=16)
    table.add_column("Surahs", width=10)
    table.add_column("Status", width=16)

    for lang_code, surah_count in sorted(stats["languages"].items()):
        name = LANG_NAMES.get(lang_code, lang_code)
        if surah_count >= 114:
            status = "[bold green]● complete[/bold green]"
        elif surah_count > 0:
            status = f"[yellow]○ {surah_count}/114[/yellow]"
        else:
            status = "[dim]○ empty[/dim]"
        table.add_row(f"{name} ({lang_code})", str(surah_count), status)

    console.print(table)

    total_langs = len(LANG_EDITIONS)
    cached_langs = len(stats["languages"])
    console.print(f"  [dim]{cached_langs}/{total_langs} languages  ·  "
                  f"{stats['total_ayahs']:,} ayahs  ·  "
                  f"{stats['size_mb']:.1f} MB on disk[/dim]")

    uncached = [l for l in LANG_EDITIONS if l not in stats["languages"]]
    if uncached:
        console.print(f"  [dim]Not cached: {', '.join(uncached)}[/dim]")
    console.print()


def _interactive_pick(all_codes: list[str], cfg: dict) -> list[str]:
    """Let user pick which languages to download."""
    from quran.ui.renderer import LANG_NAMES as UI_LANG_NAMES

    LANG_NAMES = {
        "en": "English",   "bn": "Bangla",    "ar": "Arabic",
        "ur": "Urdu",      "tr": "Turkish",   "fr": "French",
        "id": "Indonesian", "ru": "Russian",   "de": "German",
        "es": "Spanish",   "zh": "Chinese",   "nl": "Dutch",
        "ms": "Malay",
    }

    user_lang = cfg.get("lang", "en")
    defaults  = {"en"}
    if user_lang in all_codes:
        defaults.add(user_lang)

    console.print()
    console.print("  [dim]Which languages would you like to download?[/dim]")
    console.print()

    # Try interactive menu first
    try:
        from simple_term_menu import TerminalMenu

        labels = []
        for code in all_codes:
            name = LANG_NAMES.get(code, code)
            default_mark = " [green]★[/green]" if code in defaults else ""
            labels.append(f"{code:4s}  {name}{default_mark}")

        # Add "all" option at the top
        labels.insert(0, "ALL   Download all 13 languages")

        preselected = [0]  # "ALL" not preselected
        for i, code in enumerate(all_codes):
            if code in defaults:
                preselected.append(i + 1)

        console.print("  [dim]Space to select · Enter to confirm · q to cancel[/dim]\n")

        menu = TerminalMenu(
            labels,
            title="  Select languages (multi-select):",
            multi_select=True,
            show_multi_select_hint=True,
            multi_select_select_on_accept=False,
            preselected_entries=preselected,
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green", "bold"),
        )
        result = menu.show()

        if result is None:
            return []

        indices = list(result) if isinstance(result, tuple) else [result]

        if 0 in indices:
            return all_codes

        return [all_codes[i - 1] for i in indices if i > 0]

    except ImportError:
        pass

    # Fallback: text-based selection
    console.print("  [dim]Available languages:[/dim]")
    for i, code in enumerate(all_codes, 1):
        name = LANG_NAMES.get(code, code)
        default_mark = " ★" if code in defaults else ""
        console.print(f"  [green]{i:2d}[/green]  {code}  {name}{default_mark}")
    console.print(f"  [green] 0[/green]  ALL (download everything)")
    console.print()
    console.print(f"[dim]Enter numbers separated by spaces (default: {' '.join(defaults)}):[/dim] ", end="")

    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt):
        return []

    if not raw:
        return list(defaults)

    if raw == "0":
        return all_codes

    selected = []
    for part in raw.replace(",", " ").split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(all_codes):
                selected.append(all_codes[idx])
        except ValueError:
            if part in all_codes:
                selected.append(part)

    return selected or list(defaults)
