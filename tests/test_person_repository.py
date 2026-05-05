import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import skyeye.db as db_module
from skyeye.repositories.person_repository import PersonRepository


class PersonRepositoryTests(unittest.TestCase):
    def test_upserts_person_track_and_returns_gallery_ordered_by_time(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = Path(tmpdir) / "skyeye.db"
            with patch.object(db_module, "get_db_path", return_value=temp_db):
                db_module.init_db()
                conn = sqlite3.connect(temp_db)
                conn.execute("INSERT INTO videos (id, name, status) VALUES ('video-1', 'Demo', 'ready')")
                conn.execute("""
                    INSERT INTO frames (id, video_id, frame_index, timestamp, image_path, detections_json)
                    VALUES ('frame-1', 'video-1', 10, 1.0, 'frame-1.jpg', '[]')
                """)
                conn.execute("""
                    INSERT INTO frames (id, video_id, frame_index, timestamp, image_path, detections_json)
                    VALUES ('frame-2', 'video-1', 20, 2.0, 'frame-2.jpg', '[]')
                """)
                conn.commit()
                conn.close()

                repo = PersonRepository()
                person_track_id = repo.upsert_person_track(
                    video_id="video-1",
                    track_id=7,
                    start_timestamp=1.0,
                    end_timestamp=2.0,
                    summary={"class": "person"},
                )
                late_observation_id = repo.insert_observation(
                    person_track_id=person_track_id,
                    frame_id="frame-2",
                    video_id="video-1",
                    track_id=7,
                    timestamp=2.0,
                    bbox=[20, 20, 80, 120],
                    confidence=0.81,
                    crop_uri="local://persons/video-1/7/crops/obs-2.jpg",
                    context_uri="local://persons/video-1/7/contexts/obs-2.jpg",
                    quality_score=0.6,
                    is_representative=False,
                )
                early_observation_id = repo.insert_observation(
                    person_track_id=person_track_id,
                    frame_id="frame-1",
                    video_id="video-1",
                    track_id=7,
                    timestamp=1.0,
                    bbox=[10, 10, 60, 100],
                    confidence=0.91,
                    crop_uri="local://persons/video-1/7/crops/obs-1.jpg",
                    context_uri="local://persons/video-1/7/contexts/obs-1.jpg",
                    quality_score=0.9,
                    is_representative=True,
                )
                repo.set_best_observation(person_track_id, early_observation_id, 0.9)

                detail = repo.get_person_detail(person_track_id)
                gallery = repo.get_person_gallery(person_track_id)

                self.assertEqual(detail["id"], person_track_id)
                self.assertEqual(detail["track_id"], 7)
                self.assertEqual(detail["best_observation_id"], early_observation_id)
                self.assertEqual([item["id"] for item in gallery], [early_observation_id, late_observation_id])


if __name__ == "__main__":
    unittest.main()
