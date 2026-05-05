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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS person_tracks (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            start_timestamp REAL NOT NULL,
            end_timestamp REAL NOT NULL,
            best_observation_id TEXT,
            status TEXT NOT NULL DEFAULT 'ready',
            summary_json TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS track_observations (
            id TEXT PRIMARY KEY,
            person_track_id TEXT NOT NULL,
            frame_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            bbox_json TEXT NOT NULL,
            confidence REAL NOT NULL,
            crop_uri TEXT,
            context_uri TEXT,
            quality_score REAL NOT NULL DEFAULT 0,
            is_representative INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (person_track_id) REFERENCES person_tracks(id),
            FOREIGN KEY (frame_id) REFERENCES frames(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS track_representatives (
            id TEXT PRIMARY KEY,
            person_track_id TEXT NOT NULL,
            observation_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            score REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (person_track_id) REFERENCES person_tracks(id),
            FOREIGN KEY (observation_id) REFERENCES track_observations(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS person_features (
            id TEXT PRIMARY KEY,
            person_track_id TEXT NOT NULL,
            observation_id TEXT,
            extractor TEXT NOT NULL,
            model_name TEXT NOT NULL,
            model_version TEXT,
            feature_type TEXT NOT NULL,
            vector_json TEXT,
            attributes_json TEXT,
            text TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (person_track_id) REFERENCES person_tracks(id),
            FOREIGN KEY (observation_id) REFERENCES track_observations(id)
        )
    """)

    # Create index for faster searches
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id)
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_video_track ON tracks(video_id, track_id)
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_person_tracks_video_track ON person_tracks(video_id, track_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_track_observations_person_time
        ON track_observations(person_track_id, timestamp)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_track_observations_video_track
        ON track_observations(video_id, track_id)
    """)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_track_representatives_person_kind
        ON track_representatives(person_track_id, kind)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_person_features_person ON person_features(person_track_id)
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
