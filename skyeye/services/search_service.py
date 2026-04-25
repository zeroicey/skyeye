"""搜索服务"""
import json
from skyeye.db import get_db_connection


# Result deduplication settings
CONTINUOUS_GAP_SEC = 2.5
SAMPLE_INTERVAL_SEC = 6.0
IOU_THRESHOLD = 0.45

# Extended clothing keyword mappings
CLOTHING_KEYWORDS = {
    "衣服": "shirt", "衬衫": "shirt", "T恤": "t-shirt", "T恤衫": "t-shirt",
    "毛衣": "sweater", "针织衫": "sweater", "外套": "jacket", "夹克": "jacket",
    "大衣": "coat", "风衣": "coat", "羽绒服": "coat",
    "裤子": "pants", "长裤": "pants", "牛仔裤": "jeans", "牛仔": "jeans",
    "短裤": "shorts", "裙子": "skirt", "短裙": "skirt",
}

COLOR_KEYWORDS = {
    "白色": "white", "白": "white",
    "黑色": "black", "黑": "black",
    "红色": "red", "红": "red",
    "蓝色": "blue", "蓝": "blue",
    "绿色": "green", "绿": "green",
    "黄色": "yellow", "黄": "yellow",
    "深色": "dark", "深蓝": "dark", "深黑": "dark",
}


def _bbox_iou(box_a, box_b) -> float:
    """Calculate IoU for two bounding boxes in xyxy format."""
    if not box_a or not box_b or len(box_a) < 4 or len(box_b) < 4:
        return 0.0

    ax1, ay1, ax2, ay2 = box_a[:4]
    bx1, by1, bx2, by2 = box_b[:4]

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter_area

    if union <= 0:
        return 0.0
    return inter_area / union


def _same_target(current_det: dict, previous_det: dict) -> bool:
    """Judge whether two detections are likely the same target across adjacent frames."""
    if current_det.get("class") != previous_det.get("class"):
        return False

    current_bbox = current_det.get("bbox", [])
    previous_bbox = previous_det.get("bbox", [])
    return _bbox_iou(current_bbox, previous_bbox) >= IOU_THRESHOLD


def _frames_are_similar(current_frame: dict, previous_frame: dict) -> bool:
    """Two frames are similar when at least one matched detection overlaps enough."""
    current_dets = current_frame.get("detections", [])
    previous_dets = previous_frame.get("detections", [])

    for curr in current_dets:
        for prev in previous_dets:
            if _same_target(curr, prev):
                return True
    return False


def _frame_score(frame: dict) -> float:
    """Use average confidence as representative quality score."""
    detections = frame.get("detections", [])
    if not detections:
        return 0.0
    total = sum(det.get("confidence", 0.0) for det in detections)
    return total / len(detections)


def _sample_cluster(cluster_frames: list) -> list:
    """Sample keyframes from one continuous cluster to reduce visual duplicates."""
    if len(cluster_frames) <= 1:
        return cluster_frames

    selected = [cluster_frames[0]]
    next_anchor = cluster_frames[0]["timestamp"] + SAMPLE_INTERVAL_SEC
    best_candidate = None
    best_score = -1.0

    for frame in cluster_frames[1:]:
        ts = frame["timestamp"]
        score = _frame_score(frame)

        if ts < next_anchor:
            if score > best_score:
                best_candidate = frame
                best_score = score
            continue

        selected.append(best_candidate if best_candidate else frame)
        next_anchor = selected[-1]["timestamp"] + SAMPLE_INTERVAL_SEC
        best_candidate = None
        best_score = -1.0

    tail = cluster_frames[-1]
    if tail["frame_id"] != selected[-1]["frame_id"]:
        if tail["timestamp"] - selected[-1]["timestamp"] >= SAMPLE_INTERVAL_SEC * 0.8:
            selected.append(tail)

    return selected


def _deduplicate_results(results: list) -> list:
    """Group adjacent similar frames and keep only representative keyframes."""
    if not results:
        return []

    by_video = {}
    for item in results:
        by_video.setdefault(item["video_id"], []).append(item)

    reduced = []

    for video_id in by_video:
        video_results = sorted(by_video[video_id], key=lambda x: x["timestamp"])
        cluster = [video_results[0]]

        for current in video_results[1:]:
            previous = cluster[-1]
            gap = current["timestamp"] - previous["timestamp"]

            if gap <= CONTINUOUS_GAP_SEC and _frames_are_similar(current, previous):
                cluster.append(current)
            else:
                reduced.extend(_sample_cluster(cluster))
                cluster = [current]

        reduced.extend(_sample_cluster(cluster))

    reduced.sort(key=lambda x: (x["video_id"], x["timestamp"]))
    return reduced


def get_track_map(video_ids: list[str]) -> dict[tuple[str, int], dict]:
    """Load stored per-track summary rows for the selected videos."""
    if not video_ids:
        return {}

    placeholders = ",".join("?" * len(video_ids))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT video_id, track_id, best_frame_id, summary_json
        FROM tracks
        WHERE video_id IN ({placeholders})
    """, video_ids)

    track_map = {}
    for row in cursor.fetchall():
        track_map[(row["video_id"], row["track_id"])] = {
            "best_frame_id": row["best_frame_id"],
            "summary_json": row["summary_json"],
        }

    conn.close()
    return track_map


def split_tracked_results(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split matched results into tracked and untracked buckets."""
    tracked = []
    untracked = []

    for result in results:
        if result.get("track_id") is not None:
            tracked.append(result)
        else:
            untracked.append(result)

    return tracked, untracked


def group_tracked_results(results: list[dict], track_map: dict[tuple[str, int], dict]) -> list[dict]:
    """Return one representative frame result per tracked person."""
    grouped = {}

    for result in results:
        key = (result["video_id"], result["track_id"])
        grouped.setdefault(key, []).append(result)

    selected = []
    for key, items in grouped.items():
        best_frame_id = track_map.get(key, {}).get("best_frame_id")
        chosen = None

        if best_frame_id:
            for item in items:
                if item["frame_id"] == best_frame_id:
                    chosen = item
                    break

        if chosen is None:
            chosen = max(items, key=lambda item: item.get("match_confidence", 0.0))

        selected.append(chosen)

    selected.sort(key=lambda item: (item["video_id"], item["timestamp"]))
    return selected


def detect_clothing_and_colors(query: str):
    """Detect clothing categories and colors from query."""
    clothing_cats = []
    colors = []

    for cn, en in CLOTHING_KEYWORDS.items():
        if cn in query:
            if en not in clothing_cats:
                clothing_cats.append(en)

    for cn, en in COLOR_KEYWORDS.items():
        if cn in query:
            if en not in colors:
                colors.append(en)

    return clothing_cats, colors


def search_frames(video_ids: list, query: str) -> list:
    """Search frames by natural language query."""
    if not video_ids:
        return []

    query_lower = query.lower()
    clothing_cats, colors = detect_clothing_and_colors(query)

    query_words = set(query_lower.split())

    translation = {
        "人": "person", "人员": "person", "人物": "person",
        "车": "car", "汽车": "car", "车辆": "car",
        "狗": "dog", "猫": "cat",
    }

    for cn, en in translation.items():
        if cn in query_lower:
            query_words.add(en)

    placeholders = ",".join("?" * len(video_ids))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT id, video_id, frame_index, timestamp, image_path, detections_json
        FROM frames
        WHERE video_id IN ({placeholders})
        ORDER BY video_id, timestamp
    """, video_ids)

    results = []
    for row in cursor.fetchall():
        detections = json.loads(row["detections_json"]) if row["detections_json"] else []

        matched = False
        matched_detections = []

        for det in detections:
            det_class = det.get("class", "").lower()

            class_match = False
            for word in query_words:
                if word not in clothing_cats and word not in colors:
                    if word in det_class:
                        class_match = True
                        break

            clothing_match = False
            clothing_info = det.get("clothing", [])

            if clothing_info and clothing_cats:
                for clothing in clothing_info:
                    prompt = clothing.get("prompt", "").lower()
                    category = clothing.get("category", "")

                    for req_cat in clothing_cats:
                        req_type = req_cat.split()[-1] if " " in req_cat else req_cat

                        if req_type in prompt or category == req_type or req_cat in prompt:
                            if colors:
                                if any(color in prompt for color in colors):
                                    clothing_match = True
                            else:
                                clothing_match = True

                            if clothing_match:
                                break

                    if clothing_match:
                        break

            if clothing_cats:
                if clothing_match and det_class == "person":
                    matched = True
                    matched_detections.append(det)
            elif class_match:
                matched = True
                matched_detections.append(det)

        if matched:
            tracked_detections = [det for det in matched_detections if det.get("track_id") is not None]
            untracked_detections = [det for det in matched_detections if det.get("track_id") is None]

            for det in tracked_detections:
                results.append({
                    "frame_id": row["id"],
                    "video_id": row["video_id"],
                    "timestamp": round(row["timestamp"], 2),
                    "image_path": row["image_path"],
                    "detections": [det],
                    "track_id": det["track_id"],
                    "match_confidence": det.get("confidence", 0.0),
                })

            if untracked_detections:
                results.append({
                    "frame_id": row["id"],
                    "video_id": row["video_id"],
                    "timestamp": round(row["timestamp"], 2),
                    "image_path": row["image_path"],
                    "detections": untracked_detections,
                    "track_id": None,
                    "match_confidence": max(det.get("confidence", 0.0) for det in untracked_detections),
                })

    conn.close()
    track_map = get_track_map(video_ids)
    tracked_results, untracked_results = split_tracked_results(results)
    final_results = group_tracked_results(tracked_results, track_map)
    final_results.extend(_deduplicate_results(untracked_results))
    final_results.sort(key=lambda item: (item["video_id"], item["timestamp"]))
    return final_results
