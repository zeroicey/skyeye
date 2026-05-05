from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PersonImages:
    crop_jpeg: bytes
    context_jpeg: bytes


def build_person_images(frame: np.ndarray, bbox: list[float], padding_ratio: float = 0.08) -> PersonImages:
    """Build person crop and full-frame context JPEG bytes."""
    x1, y1, x2, y2 = _clamp_bbox(frame, bbox, padding_ratio)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        crop = frame

    return PersonImages(
        crop_jpeg=_encode_jpeg(crop),
        context_jpeg=_encode_jpeg(frame),
    )


def _clamp_bbox(frame: np.ndarray, bbox: list[float], padding_ratio: float) -> tuple[int, int, int, int]:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = bbox[:4]
    box_width = max(1.0, x2 - x1)
    box_height = max(1.0, y2 - y1)
    pad_x = box_width * padding_ratio
    pad_y = box_height * padding_ratio

    left = max(0, int(x1 - pad_x))
    top = max(0, int(y1 - pad_y))
    right = min(width, int(x2 + pad_x))
    bottom = min(height, int(y2 + pad_y))

    if right <= left:
        right = min(width, left + 1)
    if bottom <= top:
        bottom = min(height, top + 1)

    return left, top, right, bottom


def _encode_jpeg(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError("Failed to encode image as JPEG")
    return encoded.tobytes()
