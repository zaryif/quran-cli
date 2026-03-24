# quran-cli — Design Pattern & Interface Guide

This document defines the architectural patterns, interface design, and aesthetic rules for the `quran-cli` project. It serves as a source of truth for maintainers and AI agents.

---

## 1. The Aesthetic: "Modern Islamic Phosphor"

`quran-cli` is designed to feel like a premium, purpose-built developer tool. It draws inspiration from modern CLI tools like `gh` (GitHub CLI), `bat`, and `fd`.

- **Primary Colors**: Islamic Emerald Green (`#10b981`) and Body White (`#f0ece3`).
- **Accent Colors**: Ramadan Amber (`#f59e0b`) and Hadith Gold.
- **Background**: Deep terminal dark.
- **Typography**: Monospaced, minimal, and purposeful.

### Color Palette (Rich Markup)

| Component | Rich Markup | Usage |
|-----------|-------------|-------|
| **Emerald** | `[green]` | Primary UI, Rules, Success, Next Prayer |
| **Amber** | `[yellow]` | Arabic Text, Ramadan, Hadith Tags |
| **Dim** | `[dim]` | Labels, Hints, Footers, Secondary Info |
| **Borders** | `[bright_black]`| Table borders, separators |
| **Error** | `[red]✗[/red]` | Failure indicators |
| **Success** | `[green]✓[/green]`| Completion indicators |

---

## 2. Folder Structure

```
quran-cli/
├── quran/                 # Main package
│   ├── commands/          # CLI command implementations (one file per command)
│   ├── core/              # Business logic (API calls, algorithms, engine)
│   ├── ui/                # Shared UI rendering components
│   ├── config/            # Settings management (TOML/JSON)
│   ├── bot/               # Telegram bot implementation
│   └── connectors/        # Notification channel adapters
├── docs/                  # Extended documentation
├── tests/                 # Pytest suite
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # Main entry point
```

---

## 3. Coding Style Rules

### Variable Alignment
Module-level variables must use aligned `=` signs for readability.
```python
app     = typer.Typer()
console = Console()
```

### Comment Separators
Logical sections within a file are divided by a 80-character em-dash separator.
```python
# ── Section Title ─────────────────────────────────────────────────────────────
```

### File Header Pattern
Every command file must start with a docstring explaining the command and its usage.
```python
"""
quran <command> — short description.

Usage:
  quran <command>
"""
```

---

## 4. Interface Patterns

### Interactive Dashboards
- Use `simple-term-menu` for arrow-key navigation.
- Main dashboard: `quran` command with a looping menu.
- Titles always start with two spaces: `  Select an action:`.
- Hints are displayed in `[dim]` below the menu.

### Content Rendering
- **Arabic Text**: Always right-aligned, bold yellow, and shaped using `format_arabic()`.
- **Panels**: Ayah and Hadith text are wrapped in `Panel` with `bright_black` or `green` borders.
- **Rules**: Used to separate major sections. `Rule(style="green")` for headers, `bright_black` for content.

### Status & Loading
- Use `console.status("[dim]Loading...[/dim]")` for all network or slow operations.
- Errors are prefixed with `[red]✗[/red]` and successes with `[green]✓[/green]`.

---

*بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ*
