"""视频处理服务"""
import cv2
import uuid
import json
from pathlib import Path
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
import torch
from skyeye.paths import get_frames_dir, get_videos_dir

# Create data directories
VIDEOS_DIR = get_videos_dir()
FRAMES_DIR = get_frames_dir()

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Load YOLO model
MODEL = None
CLIP_MODEL = None
CLIP_PROCESSOR = None

# Original clothing prompts (with "a person wearing" prefix)
CLOTHING_PROMPTS = [
    "a person wearing a white shirt",
    "a person wearing a black shirt",
    "a person wearing a red shirt",
    "a person wearing a blue shirt",
    "a person wearing a green shirt",
    "a person wearing a yellow shirt",
    "a person wearing a shirt",
    "a person wearing white pants",
    "a person wearing black pants",
    "a person wearing blue jeans",
    "a person wearing dark pants",
    "a person wearing pants",
    "a person wearing a dress",
    "a person wearing a jacket",
    "a person wearing a coat",
    "a person wearing a sweater",
    "a person wearing a t-shirt",
    "a person wearing shorts",
    "a person wearing a skirt",
]


def update_track_summary(
    summaries: dict,
    video_id: str,
    track_id: int,
    timestamp: float,
    frame_id: str | None,
    confidence: float,
    bbox: list[float],
    clothing: list[dict],
    sampled: bool,
) -> None:
    """Update the aggregated summary for one tracked person."""
    summary = summaries.setdefault(
        track_id,
        {
            "video_id": video_id,
            "track_id": track_id,
            "start_timestamp": timestamp,
            "end_timestamp": timestamp,
            "best_frame_id": None,
            "sample_count": 0,
            "best_confidence": -1.0,
            "best_bbox": [],
            "best_clothing": [],
        },
    )

    summary["start_timestamp"] = min(summary["start_timestamp"], timestamp)
    summary["end_timestamp"] = max(summary["end_timestamp"], timestamp)

    if sampled:
        summary["sample_count"] += 1
        if confidence >= summary["best_confidence"]:
            summary["best_frame_id"] = frame_id
            summary["best_confidence"] = confidence
            summary["best_bbox"] = bbox
            summary["best_clothing"] = clothing


def build_track_rows(video_id: str, summaries: dict) -> list[dict]:
    """Serialize in-memory track summaries into DB-ready rows."""
    rows = []
    for summary in summaries.values():
        if summary["sample_count"] <= 0:
            continue

        rows.append(
            {
                "id": str(uuid.uuid4()),
                "video_id": video_id,
                "track_id": summary["track_id"],
                "start_timestamp": summary["start_timestamp"],
                "end_timestamp": summary["end_timestamp"],
                "best_frame_id": summary["best_frame_id"],
                "sample_count": summary["sample_count"],
                "summary_json": json.dumps(
                    {
                        "class": "person",
                        "best_confidence": summary["best_confidence"],
                        "best_bbox": summary["best_bbox"],
                        "clothing": summary["best_clothing"],
                    }
                ),
            }
        )

    return rows


def reset_tracker_state(model) -> None:
    """Reset persisted tracker state before processing a new video."""
    predictor = getattr(model, "predictor", None)
    if predictor is None:
        return

    if hasattr(predictor, "trackers"):
        predictor.trackers = None
    if hasattr(predictor, "vid_path"):
        predictor.vid_path = [None]


def get_model():
    """Get or load YOLO model."""
    global MODEL
    if MODEL is None:
        print("Loading YOLO model...")
        MODEL = YOLO("yolo26n.pt")
        # Move to GPU if available
        if torch.cuda.is_available():
            MODEL.to('cuda')
        print("YOLO model loaded!")
    return MODEL


def get_clip_model():
    """Get or load CLIP model for clothing detection."""
    global CLIP_MODEL, CLIP_PROCESSOR
    if CLIP_MODEL is None:
        print("Loading CLIP model (openai/clip-vit-base-patch32)...")
        CLIP_MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        CLIP_PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        if torch.cuda.is_available():
            CLIP_MODEL.to('cuda')
        CLIP_MODEL.eval()
        print("CLIP model loaded!")
    return CLIP_MODEL, CLIP_PROCESSOR


def detect_clothing(image_crop, prompts=None):
    """Use CLIP to detect clothing in an image crop."""
    if prompts is None:
        prompts = CLOTHING_PROMPTS

    model, processor = get_clip_model()
    image_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
    inputs = processor(text=prompts, images=image_rgb, return_tensors="pt", padding=True)

    # Move to GPU if available
    device = next(model.parameters()).device
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)[0]

    results = []
    for i, prompt in enumerate(prompts):
        conf = probs[i].item()
        if conf > 0.1:
            results.append({
                "prompt": prompt,
                "confidence": round(conf, 3),
                "category": _categorize_prompt(prompt)
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:3]


def _categorize_prompt(prompt: str) -> str:
    """Categorize prompt into clothing type."""
    prompt = prompt.lower()
    if any(w in prompt for w in ["shirt", "t-shirt", "sweater", "jacket", "coat"]):
        return "top"
    elif any(w in prompt for w in ["pants", "jeans", "shorts", "skirt"]):
        return "bottom"
    elif "dress" in prompt:
        return "dress"
    return "unknown"


def process_video(video_id: str, video_path: Path) -> dict:
    """Process video: extract frames and run YOLO + CLIP detection."""
    from skyeye.db import get_db_connection

    model = get_model()
    reset_tracker_state(model)
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {"error": "Failed to open video"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_count = 0
    saved_count = 0
    track_summaries = {}

    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"Processing video: {video_path.name}, {total_frames} frames")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        timestamp = frame_count / fps if fps else 0.0
        is_sampled_frame = frame_count % 10 == 0
        frame_id = str(uuid.uuid4()) if is_sampled_frame else None
        frame_path = None
        detections = []

        track_results = model.track(frame, verbose=False, persist=True, tracker="bytetrack.yaml")

        for result in track_results:
            boxes = result.boxes
            if boxes is None:
                continue

            for idx in range(len(boxes)):
                cls = int(boxes.cls[idx].item())
                conf = float(boxes.conf[idx].item())
                label = model.names[cls]
                bbox = boxes.xyxy[idx].tolist()

                track_id = None
                if label == "person" and boxes.id is not None:
                    track_id = int(boxes.id[idx].item())

                clothing_info = []
                if label == "person" and conf > 0.5 and is_sampled_frame:
                    x1, y1, x2, y2 = map(int, bbox)
                    h, w = frame.shape[:2]
                    x1, y1 = max(0, x1 - 10), max(0, y1 - 10)
                    x2, y2 = min(w, x2 + 10), min(h, y2 + 10)
                    person_crop = frame[y1:y2, x1:x2]
                    if person_crop.size > 0:
                        try:
                            clothing_info = detect_clothing(person_crop)
                        except Exception as e:
                            print(f"CLIP detection error: {e}")

                if track_id is not None:
                    update_track_summary(
                        summaries=track_summaries,
                        video_id=video_id,
                        track_id=track_id,
                        timestamp=timestamp,
                        frame_id=frame_id if is_sampled_frame else None,
                        confidence=conf,
                        bbox=bbox,
                        clothing=clothing_info,
                        sampled=is_sampled_frame,
                    )

                if is_sampled_frame:
                    detection = {
                        "class": label,
                        "confidence": round(conf, 2),
                        "bbox": bbox,
                        "clothing": clothing_info,
                    }
                    if track_id is not None:
                        detection["track_id"] = track_id
                    detections.append(detection)

        if is_sampled_frame:
            frame_filename = f"{frame_id}.jpg"
            frame_path = FRAMES_DIR / frame_filename
            cv2.imwrite(str(frame_path), frame)

            cursor.execute("""
                INSERT INTO frames (id, video_id, frame_index, timestamp, image_path, detections_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (frame_id, video_id, frame_count, timestamp, str(frame_path), json.dumps(detections)))
            saved_count += 1

        frame_count += 1

    cap.release()
    track_rows = build_track_rows(video_id, track_summaries)
    cursor.execute("DELETE FROM tracks WHERE video_id = ?", (video_id,))
    if track_rows:
        cursor.executemany("""
            INSERT INTO tracks (
                id, video_id, track_id, start_timestamp, end_timestamp, best_frame_id, sample_count, summary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                row["id"],
                row["video_id"],
                row["track_id"],
                row["start_timestamp"],
                row["end_timestamp"],
                row["best_frame_id"],
                row["sample_count"],
                row["summary_json"],
            )
            for row in track_rows
        ])
    cursor.execute("UPDATE videos SET status = 'ready', frame_count = ? WHERE id = ?", (saved_count, video_id))
    conn.commit()
    conn.close()

    print(f"Video processed: {saved_count} frames saved")
    return {"success": True, "frames_processed": saved_count}
