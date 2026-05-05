import cv2
import numpy as np


def blur_score(image: np.ndarray) -> float:
    """Return a Laplacian variance sharpness score."""
    if image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def score_observation(
    frame_shape: tuple[int, ...],
    bbox: list[float],
    confidence: float,
    blur_score: float,
) -> float:
    """Score how useful one tracked observation is as a representative image."""
    height, width = frame_shape[:2]
    x1, y1, x2, y2 = bbox[:4]

    box_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    frame_area = max(1.0, float(width * height))
    area_score = min(1.0, box_area / frame_area / 0.28)
    sharpness_score = min(1.0, blur_score / 160.0)
    boundary_penalty = 0.25 if _touches_boundary(width, height, bbox) else 0.0

    score = (0.45 * confidence) + (0.35 * area_score) + (0.20 * sharpness_score) - boundary_penalty
    return round(max(0.0, score), 4)


def _touches_boundary(width: int, height: int, bbox: list[float]) -> bool:
    x1, y1, x2, y2 = bbox[:4]
    margin_x = width * 0.02
    margin_y = height * 0.02
    return x1 <= margin_x or y1 <= margin_y or x2 >= width - margin_x or y2 >= height - margin_y
