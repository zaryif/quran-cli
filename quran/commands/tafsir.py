"""
quran tafsir — brief tafsir for any ayah.

Usage:
  quran tafsir 2:255
  quran tafsir 36:1-5
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.rule import Rule
from typing import Optional
from typing_extensions import Annotated

app     = typer.Typer(help="Tafsir (commentary) for any ayah.")
console = Console()


@app.callback(invoke_without_command=True, context_settings={"allow_interspersed_args": True})
def tafsir_cmd(
    ctx: typer.Context,
    ref: Annotated[Optional[str], typer.Argument(help="Ayah ref e.g. 2:255")] = None,
):
    if ctx.invoked_subcommand:
        return
    if not ref:
        console.print("[dim]Usage: quran tafsir [bold]<surah:ayah>[/bold][/dim]")
        return

    # Parse
    try:
        if ":" in ref:
            s, a = ref.split(":", 1)
            surah, ayah = int(s), int(a.split("-")[0])
        else:
            surah, ayah = int(ref), 1
    except ValueError:
        console.print(f"[red]✗[/red] Invalid reference: {ref}")
        return

    from quran.core.quran_engine import fetch_ayah, get_surah_meta

    meta = get_surah_meta(surah)
    if not meta:
        console.print(f"[red]✗[/red] Surah {surah} not found.")
        return

    with console.status(f"[dim]Loading tafsir {surah}:{ayah}…[/dim]"):
        ayah_data = fetch_ayah(surah, ayah, "en")

    if not ayah_data:
        console.print(f"[red]✗[/red] Could not fetch {surah}:{ayah}.")
        return

    console.print()
    console.print(Rule(
        f"[green]{meta['name']}[/green] [dim]{surah}:{ayah}[/dim]",
        style="bright_black"
    ))
    console.print()
    console.print(f"  [white]{ayah_data['text']}[/white]")
    console.print()

    # Fetch tafsir from API (Ibn Kathir brief edition)
    try:
        import httpx
        r = httpx.get(
            f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/editions/en.ibn-kathir",
            timeout=8.0
        )
        data = r.json()
        if data.get("status") == "OK":
            for ed in data.get("data", []):
                if ed.get("edition", {}).get("identifier") == "en.ibn-kathir":
                    tafsir_text = ed["text"][:800]
                    console.print(f"  [dim]Ibn Kathir:[/dim]")
                    console.print(f"  [dim]{tafsir_text}…[/dim]")
                    console.print()
    except Exception:
        console.print("  [dim](Tafsir requires an internet connection.)[/dim]")
        console.print()

    console.print(f"  [dim]For deeper study: islamqa.info / sunnah.com[/dim]\n")
