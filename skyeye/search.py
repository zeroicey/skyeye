import json
import re
from skyeye.db import get_db_connection

# Extended clothing keyword mappings
CLOTHING_KEYWORDS = {
    # Top clothing
    "衣服": "shirt", "衬衫": "shirt", "T恤": "t-shirt", "T恤衫": "t-shirt",
    "毛衣": "sweater", "针织衫": "sweater", "外套": "jacket", "夹克": "jacket",
    "大衣": "coat", "风衣": "coat", "羽绒服": "coat",
    # Bottom clothing
    "裤子": "pants", "长裤": "pants", "牛仔裤": "jeans", "牛仔": "jeans",
    "短裤": "shorts", "裙子": "skirt", "短裙": "skirt",
}

# Color mappings (separate for cleaner logic)
COLOR_KEYWORDS = {
    "白色": "white", "白": "white",
    "黑色": "black", "黑": "black",
    "红色": "red", "红": "red",
    "蓝色": "blue", "蓝": "blue",
    "绿色": "green", "绿": "green",
    "黄色": "yellow", "黄": "yellow",
    "深色": "dark", "深蓝": "dark", "深黑": "dark",
}


def detect_clothing_and_colors(query: str) -> tuple:
    """Detect clothing categories and colors from query.

    Returns:
        (clothing_categories, colors) - two lists
    """
    query_lower = query.lower()
    clothing_cats = []
    colors = []

    # Check clothing keywords
    for cn, en in CLOTHING_KEYWORDS.items():
        if cn in query:
            if en not in clothing_cats:
                clothing_cats.append(en)

    # Check color keywords
    for cn, en in COLOR_KEYWORDS.items():
        if cn in query:
            if en not in colors:
                colors.append(en)

    return clothing_cats, colors


def search_frames(video_ids: list, query: str) -> list:
    """Search frames by natural language query.

    Supports:
    - Basic YOLO class matching (person, car, etc.)
    - Clothing attribute matching (shirt, pants, color + clothing)
    """
    if not video_ids:
        return []

    query_lower = query.lower()

    # Detect clothing categories and colors
    clothing_cats, colors = detect_clothing_and_colors(query)

    # Extract keywords from query (for basic YOLO class matching)
    query_words = set(query_lower.split())

    # Map common Chinese to English
    translation = {
        "人": "person", "人员": "person", "人物": "person",
        "车": "car", "汽车": "car", "车辆": "car",
        "狗": "dog", "猫": "cat",
    }

    for cn, en in translation.items():
        if cn in query_lower:
            query_words.add(en)

    # Build query
    placeholders = ",".join("?" * len(video_ids))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, video_id, frame_index, timestamp, image_path, detections_json
        FROM frames
        WHERE video_id IN ({placeholders})
        ORDER BY timestamp
    """, video_ids)

    results = []
    for row in cursor.fetchall():
        detections = json.loads(row["detections_json"]) if row["detections_json"] else []

        matched = False
        matched_detections = []

        for det in detections:
            det_class = det.get("class", "").lower()

            # Check YOLO class matching (only for non-clothing keywords)
            class_match = False
            for word in query_words:
                if word not in clothing_cats and word not in colors:
                    if word in det_class:
                        class_match = True
                        break

            # Check clothing matching
            clothing_match = False
            clothing_info = det.get("clothing", [])

            if clothing_info and clothing_cats:
                for clothing in clothing_info:
                    prompt = clothing.get("prompt", "").lower()
                    category = clothing.get("category", "")

                    # Check each requested clothing category
                    for req_cat in clothing_cats:
                        # Extract clothing type (e.g., "shirt" from "white shirt")
                        req_type = req_cat.split()[-1] if " " in req_cat else req_cat

                        # Check if the clothing type matches
                        if req_type in prompt or category == req_type or req_cat in prompt:
                            # If colors specified, check color too
                            if colors:
                                if any(color in prompt for color in colors):
                                    clothing_match = True
                            else:
                                # No specific color requested, any match is OK
                                clothing_match = True

                            if clothing_match:
                                break

                    if clothing_match:
                        break

            # Determine match:
            # 1. Has clothing keywords → require clothing match
            # 2. No clothing keywords → use basic YOLO class match
            if clothing_cats:
                if clothing_match and det_class == "person":
                    matched = True
                    matched_detections.append(det)
            elif class_match:
                matched = True
                matched_detections.append(det)

        if matched:
            results.append({
                "frame_id": row["id"],
                "video_id": row["video_id"],
                "timestamp": round(row["timestamp"], 2),
                "image_path": row["image_path"],
                "detections": matched_detections
            })

    conn.close()
    return results
