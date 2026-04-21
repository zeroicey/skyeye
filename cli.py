"""SkyEye CLI - Command line tools"""
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import sqlite3
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

    conn = None
    try:
        # Clear video files
        if VIDEOS_DIR.exists():
            for f in VIDEOS_DIR.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except OSError as e:
                        typer.echo(f"⚠️  Failed to delete {f}: {e}", err=True)
            typer.echo(f"✓ Cleared {VIDEOS_DIR}")

        # Clear frame files
        if FRAMES_DIR.exists():
            for f in FRAMES_DIR.iterdir():
                if f.is_file():
                    try:
                        f.unlink()
                    except OSError as e:
                        typer.echo(f"⚠️  Failed to delete {f}: {e}", err=True)
            typer.echo(f"✓ Cleared {FRAMES_DIR}")

        # Clear database tables with transaction safety
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM frames")
            cursor.execute("DELETE FROM videos")
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise
        typer.echo("✓ Cleared database tables")

        typer.echo("\n✅ All data cleared successfully!")
    except sqlite3.Error as e:
        typer.echo(f"❌ Database error: {e}", err=True)
        raise typer.Exit(code=1)
    except OSError as e:
        typer.echo(f"❌ File operation error: {e}", err=True)
        raise typer.Exit(code=1)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    app()
