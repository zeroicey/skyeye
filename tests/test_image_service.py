import unittest

from skyeye.services.image_service import format_detection_label


class ImageServiceLabelTests(unittest.TestCase):
    def test_format_detection_label_appends_track_id(self):
        detection = {
            "class": "person",
            "confidence": 0.91,
            "track_id": 7,
            "clothing": [{"prompt": "a person wearing a red shirt", "confidence": 0.67, "category": "top"}],
        }

        label = format_detection_label(detection)

        self.assertIn("ID:7", label)
        self.assertIn("red shirt", label)

    def test_format_detection_label_works_without_track_id(self):
        detection = {"class": "car", "confidence": 0.88, "bbox": [1, 2, 3, 4], "clothing": []}

        label = format_detection_label(detection)

        self.assertNotIn("ID:", label)
        self.assertTrue(label.startswith("car"))


if __name__ == "__main__":
    unittest.main()
