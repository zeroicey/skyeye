import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import skyeye.db as db_module
import skyeye.api.persons as persons_module
from skyeye.api.persons import router as persons_router
from skyeye.repositories import PersonRepository


class PersonApiTests(unittest.TestCase):
    def test_gallery_endpoint_returns_observations_ordered_by_time(self):
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
                person_track_id = repo.upsert_person_track("video-1", 7, 1.0, 2.0, {"class": "person"})
                repo.insert_observation(
                    person_track_id, "frame-2", "video-1", 7, 2.0, [2, 2, 20, 20], 0.8,
                    "local://crop-2.jpg", "local://context-2.jpg", 0.6, False,
                )
                repo.insert_observation(
                    person_track_id, "frame-1", "video-1", 7, 1.0, [1, 1, 10, 10], 0.9,
                    "local://crop-1.jpg", "local://context-1.jpg", 0.9, True,
                )

                app = FastAPI()
                app.include_router(persons_router)
                response = TestClient(app).get(f"/api/persons/{person_track_id}/gallery")

                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual([item["timestamp"] for item in payload], [1.0, 2.0])
                self.assertEqual(payload[0]["crop_uri"], "local://crop-1.jpg")

    def test_image_endpoint_serves_local_object_uri(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "persons").mkdir()
            image_path = root / "persons" / "crop.jpg"
            image_path.write_bytes(b"fake-image")

            with patch.object(persons_module, "get_data_dir", return_value=root):
                app = FastAPI()
                app.include_router(persons_router)
                response = TestClient(app).get("/api/persons/image", params={"uri": "local://persons/crop.jpg"})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"fake-image")


if __name__ == "__main__":
    unittest.main()
