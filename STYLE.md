# quran-cli — Codebase Style Guide

> **For AI agents and contributors:** This document defines every style rule,
> pattern, color, and convention used throughout the quran-cli codebase.
> **Never deviate from these rules when adding or modifying code.**

---

```
بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ
```

---

## 1. The Aesthetic

quran-cli is inspired by tools like `git`, `gh`, `fd`, and `bat`.

> **Deep phosphor terminal dark · Islamic emerald accent · Amber for Ramadan**
> **Monospaced · Minimal · Purposeful**

Every output should feel like it belongs in a professional developer's terminal.
No clutter. No decorative fluff. Only intentional output.

---

## 2. Color Palette

These are the **only** colors used in terminal output. Reference them by their
Rich markup names or hex values. Never use raw ANSI codes.

```
╔══════════════════════════════════════════════════════════════════╗
║  COLOR          RICH MARKUP       HEX        USED FOR            ║
╠══════════════════════════════════════════════════════════════════╣
║  Islamic Green  [green]           #10b981    Primary accent       ║
║                 [bold green]                 Headers, success     ║
║                 [dim green]                  References, refs     ║
║                 [bright_black]               Borders, separators  ║
║                                                                   ║
║  Ramadan Amber  [yellow]          #f59e0b    Ramadan rows         ║
║                 [bold yellow]                Arabic text          ║
║                 [dim yellow]                 Ramadan labels       ║
║                                                                   ║
║  Hadith Gold    [yellow]◉ Hadith[/yellow]    Hadith tag           ║
║                                                                   ║
║  Error Red      [red]✗[/red]                 Errors               ║
║  Success Green  [green]✓[/green]             Success              ║
║  Warning Yellow [yellow]·[/yellow]           Warnings, bullets    ║
║                                                                   ║
║  Body White     [white]           #f0ece3    Main content text    ║
║  Dim Text       [dim]                        Labels, hints        ║
║  Dim White      [dim white]                  Secondary info       ║
╚══════════════════════════════════════════════════════════════════╝
```

### Color Rules

- `[green]` — all primary UI: section rules, success, next prayer highlight
- `[yellow]` / `[bold yellow]` — Arabic text, Ramadan rows, Hadith tags
- `[dim]` — subtitles, hints, footers, time descriptions
- `[dim green]` — hadith/ayah references like `Sahih Bukhari 1:1`
- `[bright_black]` — Rule separator borders, table borders
- `[red]✗[/red]` — errors (always the `✗` symbol)
- `[green]✓[/green]` — success (always the `✓` symbol)
- `[white]` — primary body text (ayah/hadith text inside panels)

---

## 3. Module-Level Variable Alignment

Variables at module level use **aligned spacing** — pad with spaces so `=` lines up.

```python
# ✅ CORRECT
app     = typer.Typer(help="Browse and search authentic Hadith.")
console = Console()

# ❌ WRONG
app = typer.Typer(help="Browse and search authentic Hadith.")
console = Console()
```

---

## 4. Comment Separators

Section dividers inside files use this exact format:

```python
# ── Section Title ─────────────────────────────────────────────────────────────
```

Rules:
- `# ──` to open (two em-dashes)
- Title in sentence case (not ALL CAPS, not Title Case for code sections)
- `──` padding after to fill approximately 80 columns
- One blank line before, one blank line after
- Use for: data blocks, function groups, command groups

```python
# Example usage in a file:

# ── Curated hadith index — (collection, book, number) per topic ──────────────

HADITH_TOPICS: dict = { ... }

# ── API fetch ─────────────────────────────────────────────────────────────────

def _fetch_hadith(...): ...

# ── Rendering ─────────────────────────────────────────────────────────────────

def _render(...): ...
```

---

## 5. Error & Status Patterns

### Errors

```python
# Always use this exact format:
console.print(f"[red]✗[/red] Could not load [bold]{name}[/bold].")
console.print(f"[red]✗[/red] Unknown language '[bold]{lang}[/bold]'.")
console.print(
    f"[red]✗[/red] Unknown collection '[bold]{col}[/bold]'.\n"
    f"  Options: {', '.join(options)}"
)
```

### Success

```python
console.print(f"[green]✓[/green] Saved '[bold]{label}[/bold]' → {surah}:{ayah}")
console.print(f"[green]✓[/green] Daemon started. You will receive prayer notifications.")
```

### Loading spinner

```python
# Always use [dim] style text inside status:
with console.status("[dim]Fetching today's hadith…[/dim]"):
    h = _fetch_hadith(col, book, num)

with console.status(f"[dim]Fetching {meta['name']} ({lang})…[/dim]"):
    ayahs = fetch_surah(surah_n, lang)
```

### Hints / follow-up lines

```python
# Dim green for command hints at the bottom of output:
console.print(f"  [dim]Run [green]quran hadith topics[/green] for a full list.[/dim]\n")
console.print(f"  [dim]quran bookmark goto <label>[/dim]\n")
```

---

## 6. Rich Component Styles

### Rule (section separator)

```python
# Primary sections — green
console.print(Rule("[bold]Section Title[/bold]", style="green"))

# Content rules — bright_black (dim)
console.print(Rule(
    f"[yellow]◉ Hadith[/yellow]  [dim]{h['reference']}[/dim]",
    style="bright_black"
))

# Surah header rule — green
console.print(Rule(
    f"[bold green]{meta['name']}[/bold green]  "
    f"[dim]{meta['meaning']}  ·  {meta['ayahs']} ayahs  ·  {meta['type']}[/dim]",
    style="green"
))
```

### Panel

```python
# Hadith / ayah content:
Panel(
    f"[white]{h['text']}[/white]\n\n"
    f"[dim green]— {h['reference']}  (Sahih)[/dim green]",
    title="[dim]hadith[/dim]",
    border_style="bright_black",
    padding=(1, 3),
)

# Quote (ayah of the day):
Panel(
    f"[white]{ayah['text']}[/white]\n\n[dim green]{ref}[/dim green]",
    title="[dim]random ayah[/dim]",
    border_style="green",
    padding=(1, 3),
)

# AI Guide answer:
Panel(
    result["answer"],
    title="[dim]guide answer[/dim]",
    border_style="green",
    padding=(1, 2),
)

# Info / welcome panels (green border):
Panel(
    "...",
    border_style="green",
    padding=(1, 2),
)
```

### Table

```python
# Standard table — all tables use these base settings:
Table(
    box=box.SIMPLE,
    show_header=True,
    header_style="dim",
    border_style="bright_black",
    padding=(0, 2),
)

# Table with headings (topics, schedules, surahs):
table.add_column("Topic",       width=18)
table.add_column("Count",       width=8)
table.add_column("Collection",  width=34, style="dim")
```

---

## 7. Typer Command Structure

Every command file follows this exact pattern:

```python
"""
quran <command> — one-line description.

[Optional longer description with data source info if relevant.]

Usage:
  quran <command>                    # default behavior
  quran <command> subcommand         # with subcommand
  quran <command> --flag value       # with flag
"""
from __future__ import annotations
import typer
from rich.console import Console
# ... other imports
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="One-line help string.")
console = Console()


# ── Data / constants ──────────────────────────────────────────────────────────

SOME_DATA = { ... }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _helper_fn() -> None: ...


# ── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main_cmd(ctx: typer.Context, ...):
    """Main command docstring."""
    if ctx.invoked_subcommand:
        return
    # default behavior


@app.command("sub")
def sub_cmd(...):
    """Subcommand docstring."""
    ...


# ── Interactive picker ────────────────────────────────────────────────────────

def _interactive_picker() -> None:
    try:
        from simple_term_menu import TerminalMenu
        # arrow-key menu
    except ImportError:
        # numbered fallback
```

### CLI registration in `cli.py`

```python
# Always alphabetical by command name EXCEPT:
# read, search, pray, remind, ramadan, eid
# are kept in logical/usage order at top.

app.add_typer(hadith.app,   name="hadith",   help="Browse and search authentic Hadith.")

# Pattern: app.add_typer(module.app, name="cmd", help="One sentence.")
# Alignment: name= and help= kwargs are right-padded with spaces
```

---

## 8. GUI Menu Rules (`gui.py`)

```python
# Options: plain text, 2 leading spaces, NO emoji
options = [
    "  Read Quran",
    "  Browse Hadith",
    "  Muslim World News",
    "  Exit",
]

# Title: always "  Select an action:"
menu = TerminalMenu(
    options,
    title="  Select an action:",
    menu_cursor="> ",
    menu_cursor_style=("fg_cyan", "bold"),
    menu_highlight_style=("fg_cyan", "bold"),
    clear_screen=False,
)

# Sub-menus: title describes context
menu = TerminalMenu(
    options,
    title="  Browse Hadith:",   # or "  Select a Surah:" etc.
    menu_cursor="> ",
    ...
)
```

### `_run()` function — exact signature, no modification

```python
def _run(cmd: str):
    """Execute a CLI command."""
    console.print(f"\n  [dim]→ {cmd}[/dim]\n")
    try:
        subprocess.run(cmd, shell=True)
    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
```

**Never add env manipulation, never change the signature.**

### Sub-menu pattern

```python
def _new_submenu(TerminalMenu):
    """Short description."""
    console.print()

    options = [
        "  Option one",
        "  Option two",
        "  Return to Menu",
    ]

    menu = TerminalMenu(
        options,
        title="  New Feature:",
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
        _run("quran command one")
    elif idx == 1:
        _run("quran command two")
    # idx == 2 (Return) or None → back
```

---

## 9. Interactive Picker Pattern (non-GUI commands)

Used in `namaz.py`, `hadith.py`, `connect.py`, `lang.py`:

```python
def _interactive_picker() -> None:
    console.print()
    console.print(Rule("[dim]Section Title[/dim]", style="green"))
    console.print()

    items = [...]

    try:
        from simple_term_menu import TerminalMenu

        labels = [f"{item:<20s}  extra info" for item in items]

        console.print("  [dim]↑↓ to navigate · Enter to select · q to cancel[/dim]\n")

        menu = TerminalMenu(
            labels,
            title="  Select a <thing>:",
            menu_cursor_style=("fg_green", "bold"),
            menu_highlight_style=("fg_green", "bold"),
        )
        idx = menu.show()

        if idx is None:
            console.print("  [dim]Cancelled.[/dim]")
            return

        # handle selection
        ...

    except ImportError:
        # Numbered fallback
        console.print("  [dim]Select a <thing>:[/dim]")
        for i, item in enumerate(items, 1):
            console.print(f"  [green]{i:2d}[/green]  {item}")
        console.print()
        console.print("[dim]Enter number:[/dim] ", end="")
        try:
            n = int(input().strip()) - 1
            # handle selection
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            console.print("[dim]Cancelled.[/dim]")
```

---

## 10. Navigation Hints

Bottom-of-output hints always use this format:

```python
# Single hint:
console.print(f"  [dim]quran hadith topics[/dim]\n")

# Two related hints separated by ·:
console.print(
    f"  [dim]Browse by topic: [green]quran hadith topics[/green]  ·  "
    f"Search: [green]quran hadith search <topic>[/green][/dim]\n"
)

# Three hints on one line (keep under ~80 chars):
console.print(
    f"  [dim]run [green]quran ramadan --month[/green] for full calendar[/dim]\n"
)
```

---

## 11. Notification Tag Labels

These exact strings are used as source/type labels:

```
[green]◈ Quran[/green]      — Quran ayah in guide output
[yellow]◉ Hadith[/yellow]   — Hadith in guide output and hadith command
[green]▶ next[/green]       — Next prayer in schedule
[dim]✓[/dim]                — Completed/done prayer
[yellow]☽[/yellow]          — Ramadan indicator
[green]◉[/green]            — Location indicator in header
```

---

## 12. Arabic Text Display

```python
# Always use format_arabic() from quran_engine for shaping:
from quran.core.quran_engine import format_arabic

ar_display = format_arabic(ayah["arabic"])

# Always right-align Arabic text:
from rich.align import Align
from rich.text import Text
console.print(Align.right(
    Text(ar_display, style="bold yellow", justify="right"),
    width=console.width - 4
))
```

---

## 13. Location Header (shared UI pattern)

```python
# Used at the top of pray, schedule, ramadan commands:
console.print(
    f" [green]◉[/green]  [bold]{city}, {country}[/bold]  {tag}  "
    f"[dim]{lat:.4f}°N · {lon:.4f}°E[/dim]{ram}"
)
# where tag = "[green][auto][/green]" or "[dim][manual][/dim]"
# where ram = "  [yellow]☽ Ramadan[/yellow]" or ""
```

---

## 14. Prayer/Ramadan Special Formatting

```python
# Next prayer — bold green:
f"[bold green]{name}[/bold green]"
f"[bold green]{time_str}[/bold green]  [green]▶ next[/green]"

# Ramadan rows — yellow:
f"[yellow]{name}[/yellow]"
f"[yellow]{time_str}[/yellow]"

# Done/past — dim:
f"[dim]{name}[/dim]"
f"[dim]{time_str}[/dim]"
f"[dim]✓[/dim]"

# Progress bar colors:
bar_done  = "[bright_black]{'█' * filled}{'░' * empty}[/bright_black]"  # done
bar_next  = "[green]{'█' * filled}{'░' * empty}[/green]"                # next
bar_ram   = "[yellow]{'█' * filled}{'░' * empty}[/yellow]"              # ramadan
bar_open  = "[bright_black]{'░' * bar_w}[/bright_black]"               # not started
```

---

## 15. Imports Order

```python
# 1. stdlib
from __future__ import annotations
import typer
from datetime import date, timedelta
import json
# 2. rich
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box
# 3. typing
from typing import Optional
from typing_extensions import Annotated
```

---

## 16. File Header Pattern

Every command file opens with a docstring:

```python
"""
quran <command> — short description.

Optional paragraph about data source or approach.

Usage:
  quran <command>                      # default description
  quran <command> <arg>                # with argument
  quran <command> --flag value         # with flag
  quran <command> subcommand           # subcommand
"""
```

---

## 17. Spacing Rules

```
- 2-space indent for console.print() content hints ("  [dim]...")
- Trailing \n on final console.print() of a command output block
- Blank line after Rule()
- Blank line after console.print(table)
- No trailing spaces on any line
```

---

## 18. Key File Responsibilities

```
quran/cli.py            — Entry point, registers all Typer apps
quran/commands/         — One file per user-facing command
quran/core/             — Business logic, zero UI code
quran/connectors/       — Notification channel implementations
quran/ui/renderer.py    — All Rich rendering helpers
quran/config/settings.py — TOML config read/write
quran/bot/              — Telegram bot standalone module
```

---

## 19. Versioning

```
pyproject.toml   → version = "X.Y.Z"
quran/__init__.py → __version__ = "X.Y.Z"

Both must always match.

Version bumps:
  X (major) — breaking CLI interface changes
  Y (minor) — new commands or features
  Z (patch) — bug fixes, doc updates
```

---

## 20. What Never Changes

These things are **frozen** — do not touch without explicit reason:

- `_run()` in `gui.py` — exact function body
- `BASMALLAH` string in `renderer.py`
- `SURAH_META` list in `quran_engine.py`
- `RAMADAN_STARTS` dict in `ramadan.py`
- `METHODS` dict in `prayer_times.py`
- The double-fork daemonization pattern in `scheduler.py`

---

*بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ*
