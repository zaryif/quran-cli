"""streak.py — reading and fasting streak display"""
from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich import box

console = Console()


def show_streak() -> None:
    from quran.core.streak import get

    data = get()
    rd   = data["reading"]
    fd   = data["fasting"]

    console.print()
    console.print(Rule("[dim]streaks[/dim]", style="bright_black"))
    console.print()

    def _bar(n: int, best: int, color: str) -> str:
        w    = min(n, 30)
        best_= min(best, 30) if best else 1
        bar  = f"[{color}]" + "█" * w + "[/]" + "[bright_black]" + "░" * (30 - w) + "[/]"
        return bar

    console.print(f"  [green]📖 Reading[/green]")
    console.print(f"  Current streak:  [bold green]{rd['current']}[/bold green] days")
    console.print(f"  Best streak:     [dim]{rd['best']} days[/dim]")
    console.print(f"  Total ayahs:     [dim]{rd.get('total_ayahs',0)}[/dim]")
    console.print(f"  Last read:       [dim]{rd.get('last','—')}[/dim]")
    console.print(f"  {_bar(rd['current'], rd['best'], 'green')}")
    console.print()
    console.print(f"  [yellow]☽ Fasting[/yellow]")
    console.print(f"  Current streak:  [bold yellow]{fd['current']}[/bold yellow] days")
    console.print(f"  Best streak:     [dim]{fd['best']} days[/dim]")
    console.print(f"  Last fast:       [dim]{fd.get('last','—')}[/dim]")
    console.print(f"  {_bar(fd['current'], fd['best'], 'yellow')}")
    console.print()
    console.print(f"  [dim]Mark fast: [green]quran ramadan --fast[/green][/dim]")
    console.print(f"  [dim]Streaks update automatically as you read[/dim]\n")
