"""
Interactive GUI dashboard for quran-cli.

Provides a looping, arrow-key navigable terminal dashboard with sub-menus
for reading, commands reference, and all major features.
"""
from __future__ import annotations
import sys
import subprocess
from rich.console import Console
from rich.rule import Rule
from rich.table import Table
from rich import box

console = Console()


# ── All Commands Reference ────────────────────────────────────────────────────
COMMANDS_REF = [
    ("quran",                      "Interactive dashboard"),
    ("quran read <surah>",         "Read by number: quran read 1"),
    ("quran read <name>",          "Read by name: quran read kahf"),
    ("quran read 2:255",           "Single ayah"),
    ("quran read 2:1-10",          "Ayah range"),
    ("quran read 36 --dual",       "Arabic + translation"),
    ("quran read 36 --lang bn",    "Read in Bangla"),
    ("quran search \"patience\"",  "Search across the Quran"),
    ("quran pray",                 "Prayer times for your location"),
    ("quran schedule",             "Full day schedule"),
    ("quran ramadan",              "Sehri, Iftar & Tarawih times"),
    ("quran namaz",                "Prayer performance guide"),
    ("quran lang",                 "Change display language"),
    ("quran connect",              "Notification channels"),
    ("quran guide \"...\"",        "AI Quran & Hadith guide"),
    ("quran quote",                "Daily ayah"),
    ("quran streak",               "Reading streak"),
    ("quran bookmark",             "Save reading positions"),
    ("quran tafsir",               "Tafsir for any ayah"),
    ("quran info surahs",          "List all 114 surahs"),
    ("quran info hijri",           "Today's Hijri date"),
    ("quran info location",        "Your detected location"),
    ("quran config set key val",   "Change a setting"),
    ("quran --help",               "Full help"),
]


def _get_menu():
    """Import TerminalMenu or return None."""
    try:
        from simple_term_menu import TerminalMenu
        return TerminalMenu
    except ImportError:
        return None


def show_gui():
    """Main dashboard loop."""
    from quran.ui.renderer import print_banner
    print_banner()

    TerminalMenu = _get_menu()
    if not TerminalMenu:
        console.print("  [dim]Install simple-term-menu for interactive dashboard[/dim]")
        return

    _main_menu_loop(TerminalMenu)


def _main_menu_loop(TerminalMenu):
    """Looping main menu — returns to dashboard after each action."""
    while True:
        options = [
            "  Read Quran",
            "  Search",
            "  Daily Prayer Schedule",
            "  Prayer Times",
            "  Ramadan Guide",
            "  Namaz Guide",
            "  Change Language",
            "  Notification Channels",
            "  AI Guide",
            "  All Commands",
            "  Exit",
        ]

        console.print("  [dim]↑↓ navigate · Enter select · q quit[/dim]\n")

        menu = TerminalMenu(
            options,
            title="  Select an action:",
            menu_cursor="> ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("fg_cyan", "bold"),
            clear_screen=False,
        )

        try:
            idx = menu.show()
        except KeyboardInterrupt:
            sys.exit(0)

        if idx is None or idx == len(options) - 1:
            sys.exit(0)

        actions = [
            lambda: _read_submenu(TerminalMenu),
            lambda: _search_prompt(),
            lambda: _run("quran schedule"),
            lambda: _run("quran pray"),
            lambda: _run("quran ramadan"),
            lambda: _run("quran namaz"),
            lambda: _run("quran lang"),
            lambda: _run("quran connect"),
            lambda: _run("quran guide"),
            lambda: _show_commands_ref(),
        ]

        actions[idx]()
        console.print()


def _search_prompt():
    """Prompt user for a search keyword."""
    console.print()
    console.print("  [dim]Enter a search keyword (e.g. patience, light, sabr):[/dim]")
    console.print("  > ", end="")
    try:
        query = input().strip()
    except (KeyboardInterrupt, EOFError):
        return
    if query:
        _run(f'quran search "{query}"')


def _read_submenu(TerminalMenu):
    """Sub-menu for reading the Quran."""
    console.print()

    options = [
        "  Browse Surahs (1–114)",
        "  Read by Ayah Reference",
        "  Return to Menu",
    ]

    menu = TerminalMenu(
        options,
        title="  Read Quran:",
        menu_cursor="> ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
        clear_screen=False,
    )

    try:
        idx = menu.show()
    except KeyboardInterrupt:
        return

    if idx == 0:
        _surah_browser(TerminalMenu)
    elif idx == 1:
        _read_by_ref()
    # idx == 2 or None → back


def _surah_browser(TerminalMenu):
    """Arrow-key browsable list of all 114 surahs with book-like navigation."""
    from quran.core.quran_engine import SURAH_META

    while True:
        labels = []
        for s in SURAH_META:
            num, name, meaning, ayahs, typ = s
            labels.append(f"{num:>3}.  {name:<18s}  {meaning:<30s}  {ayahs:>3} ayahs  {typ}")

        console.print()
        console.print("  [dim]↑↓ navigate · Enter to read · q back[/dim]\n")

        menu = TerminalMenu(
            labels,
            title="  Select a Surah:",
            menu_cursor="> ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("fg_cyan", "bold"),
            clear_screen=False,
        )

        try:
            idx = menu.show()
        except KeyboardInterrupt:
            return

        if idx is None:
            return

        surah_num = SURAH_META[idx][0]
        _read_with_navigation(surah_num, TerminalMenu)


def _read_with_navigation(surah_num: int, TerminalMenu):
    """Read a surah and offer book-like navigation afterwards."""
    while True:
        _run(f"quran read {surah_num} --dual")

        from quran.core.quran_engine import get_surah_meta
        meta = get_surah_meta(surah_num)
        name = meta["name"] if meta else f"Surah {surah_num}"

        nav_options = []
        if surah_num < 114:
            next_meta = get_surah_meta(surah_num + 1)
            next_name = next_meta["name"] if next_meta else f"Surah {surah_num + 1}"
            nav_options.append(f"  Next: {next_name}")
        if surah_num > 1:
            prev_meta = get_surah_meta(surah_num - 1)
            prev_name = prev_meta["name"] if prev_meta else f"Surah {surah_num - 1}"
            nav_options.append(f"  Previous: {prev_name}")
        nav_options.append("  Back to Surah List")
        nav_options.append("  Back to Main Menu")

        console.print()
        menu = TerminalMenu(
            nav_options,
            title=f"  Finished {name}:",
            menu_cursor="> ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("fg_cyan", "bold"),
            clear_screen=False,
        )

        try:
            choice = menu.show()
        except KeyboardInterrupt:
            return

        if choice is None:
            return

        selected = nav_options[choice]
        if "Next" in selected:
            surah_num += 1
        elif "Previous" in selected:
            surah_num -= 1
        elif "Surah List" in selected:
            return  # back to surah browser
        else:
            return  # back to main menu


def _read_by_ref():
    """Prompt user for an ayah reference like 2:255 or 18:1-10."""
    console.print()
    console.print("  [dim]Enter a reference (e.g. 2:255, 18:1-10, kahf):[/dim]")
    console.print("  > ", end="")
    try:
        ref = input().strip()
    except (KeyboardInterrupt, EOFError):
        return
    if ref:
        _run(f"quran read {ref} --dual")


def _show_commands_ref():
    """Display a full commands reference table."""
    console.print()
    console.print(Rule("[bold]All Commands[/bold]", style="bright_black"))
    console.print()

    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
        border_style="bright_black",
        padding=(0, 2),
        expand=False,
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="dim")

    for cmd, desc in COMMANDS_REF:
        table.add_row(cmd, desc)

    console.print(table)
    console.print()
    console.print("  [dim]Press Enter to go back…[/dim]", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def _run(cmd: str):
    """Execute a CLI command."""
    console.print(f"\n  [dim]→ {cmd}[/dim]\n")
    try:
        subprocess.run(cmd, shell=True)
    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
