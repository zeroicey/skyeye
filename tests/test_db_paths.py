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


if __name__ == "__main__":
    unittest.main()
