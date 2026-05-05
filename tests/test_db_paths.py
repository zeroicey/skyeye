import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import skyeye.db as db_module
import skyeye.paths as paths_module


class DbPathTests(unittest.TestCase):
    def test_runtime_paths_resolve_from_project_root(self):
        project_root = Path(paths_module.__file__).resolve().parent.parent
        self.assertEqual(paths_module.get_db_path(), project_root / "skyeye.db")
        self.assertEqual(paths_module.get_data_dir(), project_root / "data")
        self.assertEqual(paths_module.get_videos_dir(), project_root / "data" / "videos")
        self.assertEqual(paths_module.get_frames_dir(), project_root / "data" / "frames")

    def test_init_db_creates_tracks_table_and_unique_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = Path(tmpdir) / "skyeye.db"
            with patch.object(db_module, "get_db_path", return_value=temp_db):
                db_module.init_db()

                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'")
                self.assertEqual(cursor.fetchone()[0], "tracks")

                cursor.execute("PRAGMA index_list('tracks')")
                index_names = {row[1] for row in cursor.fetchall()}
                self.assertIn("idx_tracks_video_track", index_names)

                conn.close()

    def test_init_db_creates_person_centric_v2_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = Path(tmpdir) / "skyeye.db"
            with patch.object(db_module, "get_db_path", return_value=temp_db):
                db_module.init_db()

                conn = sqlite3.connect(temp_db)
                try:
                    cursor = conn.cursor()

                    for table_name in [
                        "person_tracks",
                        "track_observations",
                        "track_representatives",
                        "person_features",
                    ]:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                        row = cursor.fetchone()
                        self.assertIsNotNone(row)
                        self.assertEqual(row[0], table_name)

                    cursor.execute("PRAGMA index_list('person_tracks')")
                    person_track_indexes = {row[1] for row in cursor.fetchall()}
                    self.assertIn("idx_person_tracks_video_track", person_track_indexes)

                    cursor.execute("PRAGMA index_list('track_observations')")
                    observation_indexes = {row[1] for row in cursor.fetchall()}
                    self.assertIn("idx_track_observations_person_time", observation_indexes)
                    self.assertIn("idx_track_observations_video_track", observation_indexes)
                finally:
                    conn.close()


if __name__ == "__main__":
    unittest.main()
