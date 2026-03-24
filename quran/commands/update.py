"""
quran update — auto-update the CLI to the latest version.
"""
import sys
import subprocess
import typer
from rich.console import Console

app = typer.Typer(help="Update quran-cli to the latest version.")
console = Console()

@app.callback(invoke_without_command=True)
def update_cmd():
    """Download and install the latest version from GitHub."""
    import os
    
    # Check if we are in a git repository
    is_git = os.path.exists(".git")
    
    if is_git:
        console.print("\n  [dim]Detected Git repository. Pulling latest changes from main...[/dim]\n")
        try:
            subprocess.run(["git", "pull", "origin", "main"], check=True)
            console.print("\n  [green]✓[/green] Successfully pulled latest changes from GitHub.")
            console.print("  [dim]You may need to run 'pip install -e .' to apply environment changes.[/dim]\n")
            return
        except subprocess.CalledProcessError:
            console.print("\n  [yellow]![/yellow] Git pull failed. Falling back to pip install...\n")

    console.print("\n  [dim]Downloading and installing the latest version via pip...[/dim]\n")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "git+https://github.com/zaryif/quran-cli.git"],
            check=True
        )
        console.print("\n  [green]✓[/green] Successfully updated quran-cli to the latest version.")
        console.print("  [dim]Restart quran-cli to use the new features.[/dim]\n")
    except subprocess.CalledProcessError:
        console.print("\n  [red]✗[/red] Failed to update. Please check your internet connection or git installation.\n")
        raise typer.Exit(1)
