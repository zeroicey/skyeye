import cv2
import uuid
import json
import asyncio
from pathlib import Path
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
import torch

# Create data directories
DATA_DIR = Path(__file__).parent / "data"
VIDEOS_DIR = DATA_DIR / "videos"
FRAMES_DIR = DATA_DIR / "frames"

VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Load YOLO model (use nano for speed)
MODEL = None
# Load CLIP model for clothing detection
CLIP_MODEL = None
CLIP_PROCESSOR = None

# Clothing categories to detect
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


def get_model():
    """Get or load YOLO model."""
    global MODEL
    if MODEL is None:
        print("Loading YOLO model...")
        MODEL = YOLO("yolo26n.py")
        print("YOLO model loaded!")
    return MODEL


def get_clip_model():
    """Get or load CLIP model for clothing detection."""
    global CLIP_MODEL, CLIP_PROCESSOR
    if CLIP_MODEL is None:
        print("Loading CLIP model...")
        CLIP_MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        CLIP_PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        print("CLIP model loaded!")
    return CLIP_MODEL, CLIP_PROCESSOR


def detect_clothing(image_crop: cv2.Mat, prompts: list = None) -> list:
    """Use CLIP to detect clothing in an image crop.

    Args:
        image_crop: The cropped image of a person
        prompts: List of text prompts to match against

    Returns:
        List of detected clothing items with confidence scores
    """
    if prompts is None:
        prompts = CLOTHING_PROMPTS

    model, processor = get_clip_model()

    # Convert cv2 image (BGR) to RGB
    image_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)

    # Process inputs
    inputs = processor(text=prompts, images=image_rgb, return_tensors="pt", padding=True)

    with torch.no_grad():
        outputs = model(**inputs)
        # Get image-text similarity logits
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)[0]

    results = []
    for i, prompt in enumerate(prompts):
        conf = probs[i].item()
        if conf > 0.1:  # Threshold
            results.append({
                "prompt": prompt,
                "confidence": round(conf, 3),
                "category": categorize_prompt(prompt)
            })

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:3]  # Top 3 matches


def categorize_prompt(prompt: str) -> str:
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
    """Process video: extract frames and run YOLO detection."""
    from db import get_db_connection

    model = get_model()
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        return {"error": "Failed to open video"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_count = 0
    saved_count = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    print(f"Processing video: {video_path.name}, {total_frames} frames")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Process every 10th frame to reduce storage
        if frame_count % 10 == 0:
            frame_id = str(uuid.uuid4())
            timestamp = frame_count / fps

            # Save frame image
            frame_filename = f"{frame_id}.jpg"
            frame_path = FRAMES_DIR / frame_filename
            cv2.imwrite(str(frame_path), frame)

            # Run YOLO detection
            results = model(frame, verbose=False)
            detections = []

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = model.names[cls]

                    bbox = box.xyxy[0].tolist()

                    # If detected as person, use CLIP to detect clothing
                    clothing_info = []
                    if label == "person" and conf > 0.5:
                        # Crop the person from the frame
                        x1, y1, x2, y2 = map(int, bbox)
                        # Add some padding
                        h, w = frame.shape[:2]
                        x1 = max(0, x1 - 10)
                        y1 = max(0, y1 - 10)
                        x2 = min(w, x2 + 10)
                        y2 = min(h, y2 + 10)

                        person_crop = frame[y1:y2, x1:x2]
                        if person_crop.size > 0:
                            # Detect clothing using CLIP
                            try:
                                clothing_info = detect_clothing(person_crop)
                            except Exception as e:
                                print(f"CLIP detection error: {e}")

                    detection = {
                        "class": label,
                        "confidence": round(conf, 2),
                        "bbox": bbox,
                        "clothing": clothing_info
                    }
                    detections.append(detection)

            # Save to database
            cursor.execute("""
                INSERT INTO frames (id, video_id, frame_index, timestamp, image_path, detections_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (frame_id, video_id, frame_count, timestamp, str(frame_path), json.dumps(detections)))

            saved_count += 1

        frame_count += 1

    cap.release()

    # Update video status
    cursor.execute("""
        UPDATE videos SET status = 'ready', frame_count = ? WHERE id = ?
    """, (saved_count, video_id))

    conn.commit()
    conn.close()

    print(f"Video processed: {saved_count} frames saved")

    return {"success": True, "frames_processed": saved_count}
