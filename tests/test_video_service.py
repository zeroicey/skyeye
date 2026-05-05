import unittest
import cv2
import numpy as np

from skyeye.services.video_service import build_track_rows, persist_person_observation, update_track_summary


class FakeObjectStore:
    def __init__(self):
        self.objects = {}

    def put_bytes(self, key, content, content_type):
        self.objects[key] = {"content": content, "content_type": content_type}
        return f"local://{key}"


class FakePersonRepository:
    def __init__(self):
        self.tracks = []
        self.observations = []
        self.best = []

    def upsert_person_track(self, video_id, track_id, start_timestamp, end_timestamp, summary):
        self.tracks.append({
            "video_id": video_id,
            "track_id": track_id,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "summary": summary,
        })
        return f"person-{track_id}"

    def insert_observation(
        self,
        person_track_id,
        frame_id,
        video_id,
        track_id,
        timestamp,
        bbox,
        confidence,
        crop_uri,
        context_uri,
        quality_score,
        is_representative,
        observation_id=None,
    ):
        observation_id = observation_id or f"obs-{len(self.observations) + 1}"
        self.observations.append({
            "id": observation_id,
            "person_track_id": person_track_id,
            "frame_id": frame_id,
            "video_id": video_id,
            "track_id": track_id,
            "timestamp": timestamp,
            "bbox": bbox,
            "confidence": confidence,
            "crop_uri": crop_uri,
            "context_uri": context_uri,
            "quality_score": quality_score,
            "is_representative": is_representative,
        })
        return observation_id

    def set_best_observation(self, person_track_id, observation_id, score):
        self.best.append((person_track_id, observation_id, score))


class VideoServiceTrackSummaryTests(unittest.TestCase):
    def test_persist_person_observation_writes_crop_context_and_best_observation(self):
        frame = np.zeros((120, 180, 3), dtype=np.uint8)
        frame[20:100, 60:130] = (240, 240, 240)
        repo = FakePersonRepository()
        store = FakeObjectStore()
        best_scores = {}

        observation_id = persist_person_observation(
            repo=repo,
            object_store=store,
            best_scores=best_scores,
            video_id="video-1",
            frame_id="frame-1",
            frame=frame,
            timestamp=1.5,
            detection={
                "class": "person",
                "confidence": 0.91,
                "bbox": [60, 20, 130, 100],
                "track_id": 7,
                "clothing": [{"prompt": "a person wearing a white shirt", "confidence": 0.7, "category": "top"}],
            },
        )

        self.assertEqual(observation_id, repo.observations[0]["id"])
        self.assertEqual(repo.tracks[0]["track_id"], 7)
        self.assertEqual(repo.observations[0]["person_track_id"], "person-7")
        self.assertTrue(repo.observations[0]["crop_uri"].endswith(f"/crops/{observation_id}.jpg"))
        self.assertTrue(repo.observations[0]["context_uri"].endswith(f"/contexts/{observation_id}.jpg"))
        self.assertEqual(repo.best[0][0], "person-7")
        crop_key = f"persons/video-1/person-7/crops/{observation_id}.jpg"
        self.assertIn(crop_key, store.objects)
        self.assertIsNotNone(cv2.imdecode(np.frombuffer(store.objects[crop_key]["content"], dtype=np.uint8), cv2.IMREAD_COLOR))

    def test_update_track_summary_keeps_best_sampled_frame(self):
        summaries = {}

        update_track_summary(
            summaries=summaries,
            video_id="video-1",
            track_id=7,
            timestamp=1.0,
            frame_id="frame-low",
            confidence=0.61,
            bbox=[1.0, 2.0, 3.0, 4.0],
            clothing=[{"prompt": "a person wearing a blue shirt", "confidence": 0.4, "category": "top"}],
            sampled=True,
        )
        update_track_summary(
            summaries=summaries,
            video_id="video-1",
            track_id=7,
            timestamp=2.0,
            frame_id="frame-high",
            confidence=0.92,
            bbox=[2.0, 3.0, 4.0, 5.0],
            clothing=[{"prompt": "a person wearing a red shirt", "confidence": 0.8, "category": "top"}],
            sampled=True,
        )

        self.assertEqual(summaries[7]["best_frame_id"], "frame-high")
        self.assertEqual(summaries[7]["sample_count"], 2)
        self.assertEqual(summaries[7]["start_timestamp"], 1.0)
        self.assertEqual(summaries[7]["end_timestamp"], 2.0)

    def test_build_track_rows_serializes_track_summary(self):
        summaries = {
            7: {
                "video_id": "video-1",
                "track_id": 7,
                "start_timestamp": 1.0,
                "end_timestamp": 2.0,
                "best_frame_id": "frame-high",
                "sample_count": 2,
                "best_confidence": 0.92,
                "best_bbox": [2.0, 3.0, 4.0, 5.0],
                "best_clothing": [{"prompt": "a person wearing a red shirt", "confidence": 0.8, "category": "top"}],
            }
        }

        rows = build_track_rows("video-1", summaries)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["video_id"], "video-1")
        self.assertEqual(rows[0]["track_id"], 7)
        self.assertEqual(rows[0]["best_frame_id"], "frame-high")
        self.assertIn("best_confidence", rows[0]["summary_json"])


if __name__ == "__main__":
    unittest.main()
