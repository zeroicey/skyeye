import unittest

from skyeye.services.video_service import build_track_rows, update_track_summary


class VideoServiceTrackSummaryTests(unittest.TestCase):
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
