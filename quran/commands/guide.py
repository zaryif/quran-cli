"""
quran guide — AI-powered Quran & Hadith assistant.

Usage:
  quran guide "how to perform wudu"
  quran guide "what does the Quran say about patience"
  quran guide --hadith "virtues of Salah"
  quran guide --quran "signs of Day of Judgment"
  quran guide --interactive
  quran guide --offline "what is tawakkul"
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="AI-powered Quran & Hadith guide.")
console = Console()


@app.callback(invoke_without_command=True)
def guide_cmd(
    ctx:         typer.Context,
    query:       Annotated[Optional[str], typer.Argument(help="Your question")] = None,
    hadith_only: Annotated[bool, typer.Option("--hadith",  help="Search hadith only")] = False,
    quran_only:  Annotated[bool, typer.Option("--quran",   help="Search Quran only")] = False,
    offline:     Annotated[bool, typer.Option("--offline", help="BM25 sources only, no LLM")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i", help="Multi-turn chat")] = False,
):
    if ctx.invoked_subcommand:
        return

    if interactive:
        _interactive_mode(hadith_only, quran_only, offline)
        return

    if not query:
        console.print()
        console.print(Panel(
            "[bold green]quran guide[/bold green] — Ask anything about Islam.\n\n"
            "[dim]Answers are grounded in authentic Quran verses and Hadith.\n"
            "Every claim is cited. Only Sahih/Hasan hadith used.[/dim]\n\n"
            "  [dim]quran guide [/dim][green]\"how to perform wudu\"[/green]\n"
            "  [dim]quran guide [/dim][green]\"what does Quran say about patience\"[/green]\n"
            "  [dim]quran guide --hadith [/dim][green]\"virtues of Salah\"[/green]\n"
            "  [dim]quran guide --interactive[/dim]  [green]← multi-turn chat[/green]\n"
            "  [dim]quran guide --offline [/dim][green]\"tawakkul\"[/green][dim] ← no API needed[/dim]",
            border_style="green", padding=(1, 2),
        ))
        return

    _ask(query, hadith_only, quran_only, offline)


def _ask(query: str, hadith_only: bool, quran_only: bool, offline: bool) -> None:
    from quran.core.ai.rag_engine import RAGEngine

    source_filter = "hadith" if hadith_only else ("quran" if quran_only else None)

    with console.status("[dim]Searching Quran and Hadith corpus…[/dim]"):
        engine = RAGEngine()
        result = engine.answer(query, source_filter=source_filter, use_llm=not offline)

    console.print()
    console.print(Rule(f"[dim]{query[:60]}[/dim]", style="bright_black"))
    console.print()

    # Show AI answer if available
    if result.get("answer"):
        console.print(Panel(
            result["answer"],
            title="[dim]guide answer[/dim]",
            border_style="green",
            padding=(1, 2),
        ))
    elif result.get("error"):
        console.print(f"  [yellow]⚠[/yellow]  {result['error']}")
    else:
        console.print("  [dim]Offline mode — showing source passages only.[/dim]")

    # Show sources
    sources = result.get("sources", [])
    if sources:
        console.print()
        console.print(f"  [dim]Sources ({len(sources)}):[/dim]")
        for s in sources:
            tag   = "[green]◈ Quran[/green]" if s["source"] == "quran" else "[yellow]◉ Hadith[/yellow]"
            ref   = s["reference"]
            text  = s["text"][:140] + ("…" if len(s["text"]) > 140 else "")
            console.print(f"\n  {tag}  [bold]{ref}[/bold]")
            console.print(f"  [dim]{text}[/dim]")

    console.print()

    if not result.get("answer") and not result.get("error"):
        console.print("  [dim]Set [green]ANTHROPIC_API_KEY[/green] for AI-generated answers.[/dim]")
    console.print()


def _interactive_mode(hadith_only: bool, quran_only: bool, offline: bool) -> None:
    from quran.core.ai.rag_engine import RAGEngine

    engine = RAGEngine()
    source_filter = "hadith" if hadith_only else ("quran" if quran_only else None)

    console.print()
    console.print(Panel(
        "[bold green]quran guide — Interactive mode[/bold green]\n\n"
        "[dim]Ask any question about Islam.\n"
        "Type [bold]exit[/bold] or [bold]quit[/bold] to leave.[/dim]",
        border_style="green", padding=(1, 2),
    ))
    console.print()

    while True:
        try:
            console.print("[green]>[/green] ", end="")
            query = input().strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye. Assalamu alaykum.[/dim]")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q", "bye"):
            console.print("[dim]Goodbye. Assalamu alaykum.[/dim]")
            break

        _ask(query, hadith_only, quran_only, offline)
