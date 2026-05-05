import unittest

import cv2
import numpy as np

from skyeye.pipeline.cropper import build_person_images
from skyeye.pipeline.representative import score_observation


class PersonPipelineTests(unittest.TestCase):
    def test_build_person_images_returns_crop_and_context_jpegs(self):
        frame = np.zeros((120, 180, 3), dtype=np.uint8)
        frame[:, :] = (20, 40, 80)
        frame[30:100, 50:110] = (230, 240, 250)

        result = build_person_images(frame, [50, 30, 110, 100])

        crop = cv2.imdecode(np.frombuffer(result.crop_jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        context = cv2.imdecode(np.frombuffer(result.context_jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)

        self.assertIsNotNone(crop)
        self.assertIsNotNone(context)
        self.assertLess(crop.shape[0], frame.shape[0])
        self.assertLess(crop.shape[1], frame.shape[1])
        self.assertEqual(context.shape[:2], frame.shape[:2])

    def test_score_observation_prefers_large_centered_confident_box(self):
        frame_shape = (200, 300, 3)

        strong = score_observation(
            frame_shape=frame_shape,
            bbox=[80, 30, 220, 190],
            confidence=0.92,
            blur_score=180.0,
        )
        weak = score_observation(
            frame_shape=frame_shape,
            bbox=[0, 0, 25, 40],
            confidence=0.51,
            blur_score=10.0,
        )

        self.assertGreater(strong, weak)
        self.assertGreater(strong, 0.0)


if __name__ == "__main__":
    unittest.main()
