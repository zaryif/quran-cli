"""
Interactive GUI dashboard for quran-cli.
"""
from __future__ import annotations
import sys
import subprocess
from rich.console import Console
from quran.ui.renderer import print_banner

console = Console()

def show_gui():
    """Show the splash screen and an interactive menu if no command is provided."""
    print_banner()

    try:
        from simple_term_menu import TerminalMenu
    except ImportError:
        console.print("  [dim]Hint: Install simple-term-menu for interactive dashboard[/dim]")
        return

    options = [
        "📖 Read Quran",
        "🕌 Daily Schedule",
        "🧭 Prayer Times",
        "🌙 Ramadan Guide",
        "🧎 Namaz Guide",
        "🌍 Change Language",
        "⚙️ Notification Channels",
        "🤖 AI Guide",
        "❌ Exit"
    ]

    commands = [
        "quran read 1",
        "quran schedule",
        "quran pray",
        "quran ramadan",
        "quran namaz",
        "quran lang",
        "quran connect",
        "quran guide 'Islamic reminders'",
        "exit"
    ]

    console.print("  [dim]↑↓ to navigate · Enter to select · q to quit[/dim]\n")

    menu = TerminalMenu(
        options,
        title="  Select an action:",
        menu_cursor="> ",
        menu_cursor_style=("fg_green", "bold"),
        menu_highlight_style=("fg_green", "bold"),
        clear_screen=False,
    )

    try:
        idx = menu.show()
    except KeyboardInterrupt:
        console.print("  [dim]Cancelled.[/dim]")
        sys.exit(0)

    if idx is not None:
        cmd = commands[idx]
        if cmd == "exit":
            sys.exit(0)

        # Print what we're doing
        console.print(f"  [dim]Executing: [green]{cmd}[/green][/dim]\n")
        
        try:
            subprocess.run(cmd, shell=True)
        except Exception as e:
            console.print(f"  [red]Error running command: {e}[/red]")
    else:
        # User pressed 'q' or 'Esc'
        sys.exit(0)
