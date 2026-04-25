import unittest

from skyeye.services.search_service import group_tracked_results


class SearchServiceTrackTests(unittest.TestCase):
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
