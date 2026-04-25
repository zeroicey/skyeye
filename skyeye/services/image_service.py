"""图像标注服务"""
import cv2
from pathlib import Path
from fastapi import HTTPException
from skyeye.paths import get_frames_dir


# 确保FRAMES_DIR路径正确
FRAMES_DIR = get_frames_dir()
FRAMES_DIR.mkdir(parents=True, exist_ok=True)


def format_detection_label(det: dict) -> str:
    """Build a display label for one detection."""
    label = det.get("class", "unknown")
    clothing = det.get("clothing", [])
    if clothing:
        label = f"{label}: {clothing[0]['prompt']}"

    track_id = det.get("track_id")
    if track_id is not None:
        label = f"{label} ID:{track_id}"

    conf = det.get("confidence", 0)
    return f"{label} {conf:.2f}"


def annotate_frame(image_path: str, detections: list, highlight_indices: set = None) -> str:
    """为图片绘制边界框并返回标注后的图片路径

    Args:
        image_path: 原始图片路径
        detections: 检测结果列表
        highlight_indices: 需要高亮显示的检测索引集合

    Returns:
        标注后的图片路径
    """
    if highlight_indices is None:
        highlight_indices = set()

    img = cv2.imread(image_path)
    if img is None:
        raise HTTPException(status_code=404, detail="Image not found")

    for i, det in enumerate(detections):
        bbox = det.get("bbox", [])
        if len(bbox) == 4:
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 255, 0) if i in highlight_indices else (255, 0, 0)
            thickness = 3 if i in highlight_indices else 2
            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

            label_text = format_detection_label(det)
            cv2.putText(img, label_text, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # 使用原始frame_id生成标注图片路径
    frame_id = Path(image_path).stem
    annotated_path = FRAMES_DIR / f"{frame_id}_annotated.jpg"
    cv2.imwrite(str(annotated_path), img)

    return str(annotated_path)


def parse_detection_indices(indices_str: str) -> set:
    """解析检测索引字符串"""
    if not indices_str:
        return set()
    try:
        return set(int(i) for i in indices_str.split(","))
    except ValueError:
        return set()
