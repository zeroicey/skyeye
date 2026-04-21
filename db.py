import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "skyeye.db"

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'processing',
            frame_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Frames table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            frame_index INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            image_path TEXT NOT NULL,
            detections_json TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    # Create index for faster searches
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id)
    """)

    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB on import
init_db()
