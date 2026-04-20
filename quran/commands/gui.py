"""
Interactive GUI dashboard for quran-cli.

Provides a looping, arrow-key navigable terminal dashboard with sub-menus
for reading, commands reference, and all major features.

v1.2.8: Added structured Hadith browsing with book/section selection.
        All existing code preserved unchanged.
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
    ("quran",                        "Interactive dashboard"),
    ("quran read <surah>",           "Read a surah in Arabic"),
    ("quran read <surah> --dual",    "Read side-by-side Arabic + Translation"),
    ("quran read <surah> --size",    "Text size: small, medium, large"),
    ("quran read <surah> --mode",    "Reading mode: full, ayah, page"),
    ("quran search \"patience\"",      "Search across the Quran"),
    ("quran hadith",                 "Browse Hadith (Language → Collection → Book)"),
    ("quran hadith daily",           "Hadith of the day"),
    ("quran hadith browse <edition>","Browse books within an edition"),
    ("quran hadith read <ed> <num>", "Read specific hadith"),
    ("quran hadith search \"topic\"",  "Search by curated topic"),
    ("quran browse",                 "Quick Hadith collection browser"),
    ("quran fasting",                "Today's Sahur & Iftar times"),
    ("quran fasting --week",         "7-day fasting schedule"),
    ("quran pray",                   "Prayer times for your location"),
    ("quran pray setup",             "Location & calculation method wizard"),
    ("quran clock",                  "Live prayer clock with seconds + 5-waqt"),
    ("quran lock",                   "Lock the screen (PIN or Ctrl+C)"),
    ("quran lock setup",             "Set or change screen lock PIN"),
    ("quran lock off",               "Remove screen lock PIN"),
    ("quran schedule",               "Full day Islamic schedule"),
    ("quran ramadan",                "Sehri, Iftar & Tarawih times"),
    ("quran namaz",                  "Prayer details & rakat breakdown"),
    ("quran eid",                    "Eid guide + salah steps"),
    ("quran news",                   "Muslim world headlines"),
    ("quran lang",                   "Change display language"),
    ("quran connect",                "Notification channels"),
    ("quran remind setup",           "Interactive reminder & fasting wizard"),
    ("quran remind on",              "Enable prayer reminders (daemon)"),
    ("quran guide \"...\"",            "AI Quran & Hadith guide"),
    ("quran quote",                  "Daily ayah"),
    ("quran streak",                 "Reading & fasting streaks"),
    ("quran bookmark",               "Save reading positions"),
    ("quran tafsir",                 "Tafsir for any ayah"),
    ("quran cache download",         "Download Quran for offline use"),
    ("quran info surahs",            "List all 114 surahs"),
    ("quran info hijri",             "Today's Hijri date"),
    ("quran info location",          "Your detected location"),
    ("quran update",                 "Update to latest version"),
    ("quran config set key val",     "Change a setting"),
    ("quran --help",                 "Full help"),
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
            "  Browse Hadith",
            "  Read Quran with Translation",
            "  ─────────────────────────────",
            "  Daily Prayer Schedule",
            "  Prayer Clock  [live · seconds]",
            "  Fasting Times",
            "  Ramadan Guide",
            "  Prayer Details",
            "  Eid Guide",
            "  ─────────────────────────────",
            "  Search",
            "  AI Guide",
            "  Muslim World News",
            "  ─────────────────────────────",
            "  Reading Streak",
            "  Bookmarks",
            "  ─────────────────────────────",
            "  Reminder Setup Wizard",
            "  Prayer Times Setup",
            "  Change Language",
            "  Notification Channels",
            "  ─────────────────────────────",
            "  All Commands",
            "  Run Command",
            "  Update quran-cli",
            "  Lock Screen",
            "  Lock Screen Setup",
            "  ─────────────────────────────",
            "  Exit",
        ]

        # Separator indices (not selectable)
        _seps = {3, 10, 14, 17, 22, 28}

        console.print("  [dim]↑↓ navigate · Enter select · q quit[/dim]\n")

        menu = TerminalMenu(
            options,
            title="  Select an action:",
            menu_cursor="> ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("fg_cyan", "bold"),
            clear_screen=False,
            skip_empty_entries=True,
        )

        try:
            idx = menu.show()
        except KeyboardInterrupt:
            sys.exit(0)

        if idx is None or idx == len(options) - 1:
            sys.exit(0)

        if idx in _seps:
            continue

        actions = {
            0:  lambda: _read_submenu(TerminalMenu),               # Read Quran
            1:  lambda: _hadith_submenu(TerminalMenu),             # Browse Hadith
            2:  lambda: _read_with_translation_flow(TerminalMenu), # Read with Translation
            4:  lambda: _run("quran schedule"),                    # Daily Prayer Schedule
            5:  lambda: _run("quran clock"),                       # Prayer Clock
            6:  lambda: _run("quran fasting"),                     # Fasting Times
            7:  lambda: _run("quran ramadan"),                     # Ramadan Guide
            8:  lambda: _run("quran namaz"),                       # Prayer Details
            9:  lambda: _run("quran eid"),                         # Eid Guide
            11: lambda: _search_prompt(),                          # Search
            12: lambda: _run("quran guide"),                       # AI Guide
            13: lambda: _news_submenu(TerminalMenu),               # Muslim World News
            15: lambda: _run("quran streak"),                      # Reading Streak
            16: lambda: _run("quran bookmark"),                    # Bookmarks
            18: lambda: _run("quran remind setup"),                # Reminder Setup Wizard
            19: lambda: _run("quran pray setup"),                  # Prayer Times Setup
            20: lambda: _run("quran lang"),                        # Change Language
            21: lambda: _run("quran connect"),                     # Notification Channels
            23: lambda: _show_commands_ref(),                      # All Commands
            24: lambda: _run_any_command(),                        # Run Command
            25: lambda: _run("quran update"),                      # Update quran-cli
            26: lambda: _run("quran lock"),                        # Lock Screen
            27: lambda: _run("quran lock setup"),                  # Lock Screen Setup
        }

        action = actions.get(idx)
        if action:
            action()
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


def _run_any_command():
    """Prompt user for any raw quran command."""
    console.print()
    console.print("  [dim]Enter any quran command (e.g. read 18, quote, search light):[/dim]")
    console.print("  > quran ", end="")
    try:
        cmd = input().strip()
    except (KeyboardInterrupt, EOFError):
        return
    if cmd:
        _run(f"quran {cmd}")


def _read_submenu(TerminalMenu):
    """Sub-menu for reading the Quran."""
    console.print()

    options = [
        "  Browse Surahs (1–114)        [dim](Full Surah)[/dim]",
        "  Read Ayah-by-Ayah          [dim](Interactive)[/dim]",
        "  Read by Ayah Reference",
        "  Advanced Reader Wizard     [dim](Size, Dual, Mode)[/dim]",
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
        _surah_browser(TerminalMenu, mode="full")
    elif idx == 1:
        _surah_browser(TerminalMenu, mode="ayah")
    elif idx == 2:
        _read_by_ref()
    elif idx == 3:
        _run("quran read")
    # idx == 4 or None → back


def _surah_browser(TerminalMenu, mode="full"):
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
        
        if mode == "ayah":
            _run(f"quran read {surah_num} --mode ayah")
        else:
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


def _hadith_submenu(TerminalMenu):
    """Sub-menu for browsing Hadith."""
    console.print()

    options = [
        "  [bold]Browse Collections[/bold]        [dim](Bukhari, Muslim, etc.)[/dim]",
        "  [bold]Hadith of the Day[/bold]         [dim](Daily rotation)[/dim]",
        "  [bold]Search Topics[/bold]             [dim](Patience, Prayer, etc.)[/dim]",
        "  [back] Return to Menu[/back]",
    ]

    menu = TerminalMenu(
        options,
        title="  Browse Hadith:",
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
        _run("quran hadith")
    elif idx == 1:
        _run("quran hadith daily")
    elif idx == 2:
        console.print()
        console.print("  [dim]Enter a topic (e.g. patience, prayer, fasting, tawakkul):[/dim]")
        console.print("  > ", end="")
        try:
            kw = input().strip()
            if kw:
                _run(f'quran hadith search "{kw}"')
        except (KeyboardInterrupt, EOFError):
            pass
    # idx == 3 is Return to Menu
    # idx == 4 or None → back


def _news_submenu(TerminalMenu):
    """Sub-menu for selecting a news source."""
    console.print()

    options = [
        "  Al Jazeera  — global Muslim world news",
        "  Seekers     — SeekersGuidance Islamic knowledge",
        "  5Pillars    — British Muslim news",
        "  IslamQA     — Islamic rulings & Q&A",
        "  Return to Menu",
    ]

    menu = TerminalMenu(
        options,
        title="  Muslim World News — select source:",
        menu_cursor="> ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
        clear_screen=False,
    )

    try:
        idx = menu.show()
    except KeyboardInterrupt:
        return

    source_map = {0: "aljazeera", 1: "seekers", 2: "5pillars", 3: "islamqa"}
    if idx is not None and idx in source_map:
        _run(f"quran news --source {source_map[idx]}")
    # idx == 4 or None → back


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


def _read_with_translation_flow(TerminalMenu):
    """Flow for 'Read Quran with Translation': Select L1 -> Select L2 -> Select Surah -> Read."""
    from quran.core.quran_engine import LANG_EDITIONS, SURAH_META
    from quran.commands.lang import LANGUAGES

    # 1. Select Language 1
    lang_items = list(LANG_EDITIONS.keys())
    lang_labels = []
    for code in lang_items:
        name = LANGUAGES.get(code, {}).get("native", code)
        lang_labels.append(f"{code:4s}  {name}")

    l1_menu = TerminalMenu(
        lang_labels,
        title="  Select First Language (Left):",
        menu_cursor="> ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
    )
    l1_idx = l1_menu.show()
    if l1_idx is None:
        return
    l1 = lang_items[l1_idx]

    # 2. Select Language 2
    l2_menu = TerminalMenu(
        lang_labels,
        title=f"  Select Second Language (Right) [L1: {l1}]:",
        menu_cursor="> ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan", "bold"),
    )
    l2_idx = l2_menu.show()
    if l2_idx is None:
        return
    l2 = lang_items[l2_idx]

    # 3. Select Surah
    surah_labels = []
    for s in SURAH_META:
        num, name, meaning, ayahs, typ = s
        surah_labels.append(f"{num:>3}.  {name:<18s}  {meaning}")

    s_menu = TerminalMenu(
        surah_labels,
        title=f"  Select Surah ({l1} + {l2}):",
        show_search_hint=True,
        menu_cursor="> ",
        menu_cursor_style=("fg_cyan", "bold"),
    )
    s_idx = s_menu.show()
    if s_idx is None:
        return
    surah_num = SURAH_META[s_idx][0]

    # 4. Command Dispatch Logic
    if l1 == l2:
        cmd = f"quran read {surah_num} --lang {l1}"
    elif l1 == "ar":
        cmd = f"quran read {surah_num} --dual --lang {l2}"
    elif l2 == "ar":
        cmd = f"quran read {surah_num} --dual --lang {l1}"
    else:
        cmd = f"quran read {surah_num} --dual2 --lang {l1} --lang2 {l2}"

    _run(cmd)

    # Wait for user to read before returning to menu
    console.print("\n  [dim]Press Enter to return to menu…[/dim]", end="")
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
