"""SkyEye CLI - Command line tools"""
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import typer

from db import get_db_connection
from services import VIDEOS_DIR, FRAMES_DIR

app = typer.Typer(help="SkyEye CLI")


@app.command()
def hello(name: str = "World"):
    """Say hello."""
    typer.echo(f"Hello, {name}!")


@app.command(name="clear-all")
def clear_all(yes: bool = typer.Option(False, "--yes", help="Skip confirmation")):
    """Clear all video, frame data and reset database."""
    # Confirmation
    if not yes:
        typer.echo("⚠️  This will delete ALL videos, frames, and reset the database.")
        confirm = typer.prompt("Type 'yes' to confirm")
        if confirm != "yes":
            typer.echo("Cancelled.")
            raise typer.Exit(code=0)

    try:
        # Clear video files
        if VIDEOS_DIR.exists():
            for f in VIDEOS_DIR.iterdir():
                if f.is_file():
                    f.unlink()
            typer.echo(f"✓ Cleared {VIDEOS_DIR}")

        # Clear frame files
        if FRAMES_DIR.exists():
            for f in FRAMES_DIR.iterdir():
                if f.is_file():
                    f.unlink()
            typer.echo(f"✓ Cleared {FRAMES_DIR}")

        # Clear database tables
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM frames")
        cursor.execute("DELETE FROM videos")
        conn.commit()
        conn.close()
        typer.echo("✓ Cleared database tables")

        typer.echo("\n✅ All data cleared successfully!")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
