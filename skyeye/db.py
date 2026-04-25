import sqlite3

from skyeye.paths import get_db_path

def init_db():
    """Initialize the database."""
    conn = sqlite3.connect(get_db_path())
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            start_timestamp REAL NOT NULL,
            end_timestamp REAL NOT NULL,
            best_frame_id TEXT,
            sample_count INTEGER NOT NULL DEFAULT 0,
            summary_json TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (best_frame_id) REFERENCES frames(id)
        )
    """)

    # Create index for faster searches
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id)
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_video_track ON tracks(video_id, track_id)
    """)

    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB on import
init_db()
