# ByteTrack Minimal Backend Retrofit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-video person tracking with ByteTrack, store lightweight track summaries, and return track-level person search results with minimal backend changes.

**Architecture:** Introduce a shared runtime path module, extend SQLite with a lightweight `tracks` table, run tracking on every frame while persisting sampled frames, and group matched person results by `(video_id, track_id)` in the search service. Keep frame-level JSON detections and preserve the old fallback deduplication path for untracked detections.

**Tech Stack:** Python 3.14, FastAPI, SQLite, OpenCV, Ultralytics YOLO tracking, Transformers CLIP, unittest

---

## File Map

- Create: `skyeye/paths.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db_paths.py`
- Create: `tests/test_video_service.py`
- Create: `tests/test_search_service.py`
- Create: `tests/test_image_service.py`
- Modify: `skyeye/db.py`
- Modify: `skyeye/services/video_service.py`
- Modify: `skyeye/services/search_service.py`
- Modify: `skyeye/services/image_service.py`
- Modify: `skyeye/services/__init__.py` if exports need to expose new helpers for tests

### Task 1: Canonical Runtime Paths and Track Schema

**Files:**
- Create: `skyeye/paths.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db_paths.py`
- Modify: `skyeye/db.py`
- Modify: `skyeye/services/video_service.py`
- Modify: `skyeye/services/image_service.py`

- [ ] **Step 1: Write the failing path and schema tests**

```python
# tests/test_db_paths.py
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import skyeye.db as db_module
import skyeye.paths as paths_module


class DbPathTests(unittest.TestCase):
    def test_runtime_paths_resolve_from_project_root(self):
        project_root = Path(paths_module.__file__).resolve().parent.parent
        self.assertEqual(paths_module.get_db_path(), project_root / "skyeye.db")
        self.assertEqual(paths_module.get_data_dir(), project_root / "data")
        self.assertEqual(paths_module.get_videos_dir(), project_root / "data" / "videos")
        self.assertEqual(paths_module.get_frames_dir(), project_root / "data" / "frames")

    def test_init_db_creates_tracks_table_and_unique_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_db = Path(tmpdir) / "skyeye.db"
            with patch.object(db_module, "get_db_path", return_value=temp_db):
                db_module.init_db()

                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracks'")
                self.assertEqual(cursor.fetchone()[0], "tracks")

                cursor.execute("PRAGMA index_list('tracks')")
                index_names = {row[1] for row in cursor.fetchall()}
                self.assertIn("idx_tracks_video_track", index_names)

                conn.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_db_paths -v`
Expected: FAIL because `skyeye.paths` does not exist yet and `tracks` table/index are not created.

- [ ] **Step 3: Write the minimal implementation**

```python
# skyeye/paths.py
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_db_path() -> Path:
    return get_project_root() / "skyeye.db"


def get_data_dir() -> Path:
    return get_project_root() / "data"


def get_videos_dir() -> Path:
    return get_data_dir() / "videos"


def get_frames_dir() -> Path:
    return get_data_dir() / "frames"
```

```python
# skyeye/db.py
import sqlite3

from skyeye.paths import get_db_path


def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'processing',
            frame_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS frames (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            frame_index INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            image_path TEXT NOT NULL,
            detections_json TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            track_id INTEGER NOT NULL,
            start_timestamp REAL NOT NULL,
            end_timestamp REAL NOT NULL,
            best_frame_id TEXT,
            sample_count INTEGER NOT NULL DEFAULT 0,
            summary_json TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id),
            FOREIGN KEY (best_frame_id) REFERENCES frames(id)
        )
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id)")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_video_track ON tracks(video_id, track_id)"
    )

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


init_db()
```

```python
# tests/__init__.py
```

- [ ] **Step 4: Update services to use the shared path helpers**

```python
# skyeye/services/video_service.py
from skyeye.paths import get_frames_dir, get_videos_dir

VIDEOS_DIR = get_videos_dir()
FRAMES_DIR = get_frames_dir()
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
```

```python
# skyeye/services/image_service.py
from skyeye.paths import get_frames_dir

FRAMES_DIR = get_frames_dir()
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv\Scripts\python -m unittest tests.test_db_paths -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 6: Commit**

```bash
git add tests/__init__.py tests/test_db_paths.py skyeye/paths.py skyeye/db.py skyeye/services/video_service.py skyeye/services/image_service.py
git commit -m "feat: add canonical runtime paths and track schema"
```

### Task 2: Track Summary Aggregation in Video Processing

**Files:**
- Create: `tests/test_video_service.py`
- Modify: `skyeye/services/video_service.py`

- [ ] **Step 1: Write the failing track summary tests**

```python
# tests/test_video_service.py
import unittest

from skyeye.services.video_service import update_track_summary, build_track_rows


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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_video_service -v`
Expected: FAIL because `update_track_summary` and `build_track_rows` do not exist.

- [ ] **Step 3: Write the minimal track summary helpers**

```python
# skyeye/services/video_service.py
import json
import uuid


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
```

- [ ] **Step 4: Wire processing to tracking and track row persistence**

```python
# skyeye/services/video_service.py
track_summaries = {}

# inside the frame loop
track_results = model.track(frame, verbose=False, persist=True, tracker="bytetrack.yaml")

for result in track_results:
    boxes = result.boxes
    track_ids = boxes.id.tolist() if boxes.id is not None else [None] * len(boxes)
    for box, track_id_tensor in zip(boxes, track_ids):
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        label = model.names[cls]
        bbox = box.xyxy[0].tolist()
        track_id = int(track_id_tensor) if track_id_tensor is not None and label == "person" else None

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
                except Exception as exc:
                    print(f"CLIP detection error: {exc}")

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
```

```python
# after the frame loop and before marking the video ready
track_rows = build_track_rows(video_id, track_summaries)
cursor.executemany(
    """
    INSERT OR REPLACE INTO tracks (
        id, video_id, track_id, start_timestamp, end_timestamp, best_frame_id, sample_count, summary_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    [
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
    ],
)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python -m unittest tests.test_video_service -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 6: Commit**

```bash
git add tests/test_video_service.py skyeye/services/video_service.py
git commit -m "feat: add track summary aggregation"
```

### Task 3: Track-Aware Search Results

**Files:**
- Create: `tests/test_search_service.py`
- Modify: `skyeye/services/search_service.py`

- [ ] **Step 1: Write the failing search grouping tests**

```python
# tests/test_search_service.py
import unittest

from skyeye.services.search_service import group_tracked_results


class SearchServiceTrackTests(unittest.TestCase):
    def test_group_tracked_results_returns_one_result_per_track(self):
        results = [
            {
                "frame_id": "frame-1",
                "video_id": "video-1",
                "timestamp": 1.0,
                "track_id": 7,
                "match_confidence": 0.61,
                "detections": [{"class": "person", "confidence": 0.61, "bbox": [1, 2, 3, 4], "track_id": 7}],
            },
            {
                "frame_id": "frame-2",
                "video_id": "video-1",
                "timestamp": 2.0,
                "track_id": 7,
                "match_confidence": 0.91,
                "detections": [{"class": "person", "confidence": 0.91, "bbox": [1, 2, 3, 4], "track_id": 7}],
            },
        ]
        track_map = {("video-1", 7): {"best_frame_id": "frame-2"}}

        grouped = group_tracked_results(results, track_map)

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["frame_id"], "frame-2")
        self.assertEqual(grouped[0]["track_id"], 7)

    def test_group_tracked_results_falls_back_to_highest_match_confidence(self):
        results = [
            {
                "frame_id": "frame-1",
                "video_id": "video-1",
                "timestamp": 1.0,
                "track_id": 8,
                "match_confidence": 0.83,
                "detections": [{"class": "person", "confidence": 0.83, "bbox": [1, 2, 3, 4], "track_id": 8}],
            },
            {
                "frame_id": "frame-2",
                "video_id": "video-1",
                "timestamp": 2.0,
                "track_id": 8,
                "match_confidence": 0.63,
                "detections": [{"class": "person", "confidence": 0.63, "bbox": [1, 2, 3, 4], "track_id": 8}],
            },
        ]

        grouped = group_tracked_results(results, {})

        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["frame_id"], "frame-1")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_search_service -v`
Expected: FAIL because `group_tracked_results` does not exist.

- [ ] **Step 3: Write the minimal grouping helpers**

```python
# skyeye/services/search_service.py
def group_tracked_results(results: list[dict], track_map: dict[tuple[str, int], dict]) -> list[dict]:
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


def split_tracked_results(results: list[dict]) -> tuple[list[dict], list[dict]]:
    tracked = []
    untracked = []
    for result in results:
        if result.get("track_id") is not None:
            tracked.append(result)
        else:
            untracked.append(result)
    return tracked, untracked
```

- [ ] **Step 4: Integrate the grouping into `search_frames`**

```python
# skyeye/services/search_service.py
def get_track_map(video_ids: list[str]) -> dict[tuple[str, int], dict]:
    placeholders = ",".join("?" * len(video_ids))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT video_id, track_id, best_frame_id, summary_json
        FROM tracks
        WHERE video_id IN ({placeholders})
        """,
        video_ids,
    )

    track_map = {}
    for row in cursor.fetchall():
        track_map[(row["video_id"], row["track_id"])] = {
            "best_frame_id": row["best_frame_id"],
            "summary_json": row["summary_json"],
        }

    conn.close()
    return track_map
```

```python
# inside search_frames, when building matched frame results
if matched:
    track_id = None
    if matched_detections and matched_detections[0].get("track_id") is not None:
        track_id = matched_detections[0]["track_id"]

    results.append(
        {
            "frame_id": row["id"],
            "video_id": row["video_id"],
            "timestamp": round(row["timestamp"], 2),
            "image_path": row["image_path"],
            "detections": matched_detections,
            "track_id": track_id,
            "match_confidence": max(det.get("confidence", 0.0) for det in matched_detections),
        }
    )

track_map = get_track_map(video_ids)
tracked, untracked = split_tracked_results(results)
grouped = group_tracked_results(tracked, track_map)
return grouped + _deduplicate_results(untracked)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python -m unittest tests.test_search_service -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 6: Commit**

```bash
git add tests/test_search_service.py skyeye/services/search_service.py
git commit -m "feat: group person search results by track"
```

### Task 4: Track IDs in Detection Payloads and Annotated Frames

**Files:**
- Create: `tests/test_image_service.py`
- Modify: `skyeye/services/video_service.py`
- Modify: `skyeye/services/image_service.py`

- [ ] **Step 1: Write the failing image label tests**

```python
# tests/test_image_service.py
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_image_service -v`
Expected: FAIL because `format_detection_label` does not exist.

- [ ] **Step 3: Write the minimal label formatter and use it**

```python
# skyeye/services/image_service.py
def format_detection_label(det: dict) -> str:
    label = det.get("class", "unknown")
    clothing = det.get("clothing", [])
    if clothing:
        label = f"{label}: {clothing[0]['prompt']}"

    track_id = det.get("track_id")
    if track_id is not None:
        label = f"{label} ID:{track_id}"

    conf = det.get("confidence", 0)
    return f"{label} {conf:.2f}"
```

```python
# skyeye/services/image_service.py inside annotate_frame
label_text = format_detection_label(det)
cv2.putText(img, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
```

- [ ] **Step 4: Store `track_id` on sampled person detections**

```python
# skyeye/services/video_service.py when building each detection
detection = {
    "class": label,
    "confidence": round(conf, 2),
    "bbox": bbox,
    "clothing": clothing_info,
}
if track_id is not None:
    detection["track_id"] = track_id
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv\Scripts\python -m unittest tests.test_image_service -v`
Expected: PASS with 2 passing tests.

- [ ] **Step 6: Run the focused suite**

Run: `.venv\Scripts\python -m unittest tests.test_db_paths tests.test_video_service tests.test_search_service tests.test_image_service -v`
Expected: PASS with all targeted tests green.

- [ ] **Step 7: Commit**

```bash
git add tests/test_image_service.py skyeye/services/video_service.py skyeye/services/image_service.py
git commit -m "feat: surface track ids in detections and annotations"
```

## Self-Review Checklist

- Spec coverage:
  - Canonical runtime paths and `tracks` schema are covered in Task 1.
  - Track summary aggregation and persistence are covered in Task 2.
  - Track-aware search grouping is covered in Task 3.
  - Detection payload and annotated frame `track_id` display are covered in Task 4.
- Placeholder scan:
  - No `TODO`, `TBD`, or `...` placeholders remain.
- Type consistency:
  - Track summaries consistently use `track_id: int`, `best_frame_id: str | None`, and `summary_json: str`.
  - Search grouping consistently keys on `(video_id, track_id)`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-25-bytetrack-minimal-backend-retrofit.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Because you asked me to implement directly in this session and did not ask for subagents, the next step is **Inline Execution**.
