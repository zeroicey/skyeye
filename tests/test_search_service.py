import unittest

from skyeye.services.search_service import enrich_person_results, group_tracked_results


class SearchServiceTrackTests(unittest.TestCase):
    def test_enrich_person_results_adds_person_centric_fields(self):
        results = [
            {
                "frame_id": "frame-1",
                "video_id": "video-1",
                "timestamp": 1.0,
                "track_id": 7,
                "match_confidence": 0.91,
                "detections": [{"class": "person", "confidence": 0.91, "bbox": [1, 2, 3, 4], "track_id": 7}],
            }
        ]
        person_index = {
            ("video-1", 7): {
                "person_track_id": "person-7",
                "start_timestamp": 0.5,
                "end_timestamp": 3.0,
                "crop_uri": "local://persons/video-1/person-7/crops/best.jpg",
                "context_uri": "local://persons/video-1/person-7/contexts/best.jpg",
                "summary": {"class": "person"},
            }
        }

        enriched = enrich_person_results(results, person_index)

        self.assertEqual(enriched[0]["person_track_id"], "person-7")
        self.assertEqual(enriched[0]["crop_uri"], "local://persons/video-1/person-7/crops/best.jpg")
        self.assertEqual(enriched[0]["context_uri"], "local://persons/video-1/person-7/contexts/best.jpg")
        self.assertEqual(enriched[0]["start_timestamp"], 0.5)
        self.assertEqual(enriched[0]["end_timestamp"], 3.0)

    def test_group_tracked_results_returns_one_result_per_track(self):
        results = [
            {
                "frame_id": "frame-1",
                "video_id": "video-1",
                "timestamp": 1.0,
                "track_id": 7,
                "match_confidence": 0.61,
                "detections": [{"class": "person", "confidence": 0.61, "bbox": [1, 2, 3, 4], "track_id": 7}],
            },
            {
                "frame_id": "frame-2",
                "video_id": "video-1",
                "timestamp": 2.0,
                "track_id": 7,
                "match_confidence": 0.91,
                "detections": [{"class": "person", "confidence": 0.91, "bbox": [1, 2, 3, 4], "track_id": 7}],
            },
        ]
        track_map = {("video-1", 7): {"best_frame_id": "frame-2"}}

        grouped = group_tracked_results(results, track_map)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["frame_id"], "frame-2")
        self.assertEqual(grouped[0]["track_id"], 7)

    def test_group_tracked_results_falls_back_to_highest_match_confidence(self):
        results = [
            {
                "frame_id": "frame-1",
                "video_id": "video-1",
                "timestamp": 1.0,
                "track_id": 8,
                "match_confidence": 0.83,
                "detections": [{"class": "person", "confidence": 0.83, "bbox": [1, 2, 3, 4], "track_id": 8}],
            },
            {
                "frame_id": "frame-2",
                "video_id": "video-1",
                "timestamp": 2.0,
                "track_id": 8,
                "match_confidence": 0.63,
                "detections": [{"class": "person", "confidence": 0.63, "bbox": [1, 2, 3, 4], "track_id": 8}],
            },
        ]

        grouped = group_tracked_results(results, {})

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["frame_id"], "frame-1")


if __name__ == "__main__":
    unittest.main()
