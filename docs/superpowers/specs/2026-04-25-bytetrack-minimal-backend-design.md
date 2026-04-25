# ByteTrack Minimal Backend Retrofit Design

## Summary

This design adds person-level tracking to the current SkyEye backend with the smallest useful architectural change set.
The goal is to turn frame-level person detections into track-level search results inside a single video while preserving the existing FastAPI API shape and most of the current storage model.

The design intentionally does not cover cross-video identity matching, ReID, trajectory playback, vector search, or a queue system.

## Current State

The current backend processes video through this path:

1. Upload video through `/api/videos/upload`
2. Process the video asynchronously in `skyeye.services.video_service.process_video`
3. Sample one frame every 10 frames
4. Run YOLO detection on sampled frames
5. Run CLIP clothing recognition on detected persons
6. Store each sampled frame and its detections in the `frames` table
7. Search stored frames by query and deduplicate results with timestamp and IoU heuristics

This causes three user-facing problems:

1. The same person appears as many near-duplicate search results because there is no persistent identity across frames.
2. Search deduplication is heuristic and can both over-collapse and under-collapse results.
3. The backend has no durable track-level entity to summarize a person across a video.

## Goals

1. Add stable per-video `track_id` values for detected persons using ByteTrack.
2. Keep the existing frame storage and search API usable with minimal frontend changes.
3. Return person search results grouped by track rather than by raw frame whenever tracking data exists.
4. Store one lightweight track summary row per tracked person to support track-level search results.
5. Keep non-person detections working without requiring track data.

## Non-Goals

1. Cross-video identity matching
2. Multi-camera tracking
3. Full per-frame trajectory playback APIs
4. Vector embeddings or semantic retrieval changes
5. Replacing SQLite in this phase
6. Major frontend redesign

## Design Principles

1. Prefer the built-in `ultralytics` tracking mode instead of adding a separate tracker package.
2. Track on every frame for stability, but only persist sampled frames to keep storage and CLIP cost controlled.
3. Add structured track summaries now without introducing a large observation table in this phase.
4. Keep old frame-level fallback behavior for detections that do not have `track_id`.

## Architecture

### Processing Pipeline

The updated pipeline becomes:

1. Open the uploaded video.
2. Run YOLO tracking on every frame using `model.track(..., persist=True, tracker="bytetrack.yaml")`.
3. Extract tracked person detections from each frame and maintain an in-memory per-video track summary map.
4. On sampled frames only:
   1. Save the frame image.
   2. Run CLIP clothing recognition only for sampled person detections.
   3. Store detections in `frames.detections_json`, including `track_id` for tracked persons.
   4. Update the best representative sampled frame for each track.
5. After the video ends, write aggregated track summary rows to a new `tracks` table.
6. Mark the video as `ready`.

### Why Track Every Frame but Persist Every 10 Frames

ByteTrack depends on continuous temporal context.
If tracking only runs once every 10 frames, IDs will break more often and the result quality will be poor.
Running tracking on every frame gives the tracker enough continuity, while persisting only sampled frames preserves the current performance and storage behavior.

## Data Model

### Existing Tables

The existing `videos` and `frames` tables remain in place.

`frames.detections_json` keeps its current role, but person detections gain an optional `track_id` field:

```json
{
  "class": "person",
  "confidence": 0.91,
  "bbox": [100.0, 40.0, 260.0, 390.0],
  "track_id": 7,
  "clothing": [
    {
      "prompt": "a person wearing a red shirt",
      "confidence": 0.67,
      "category": "top"
    }
  ]
}
```

Non-person detections continue to omit `track_id`.

### New `tracks` Table

Add a lightweight `tracks` table:

- `id TEXT PRIMARY KEY`
- `video_id TEXT NOT NULL`
- `track_id INTEGER NOT NULL`
- `start_timestamp REAL NOT NULL`
- `end_timestamp REAL NOT NULL`
- `best_frame_id TEXT`
- `sample_count INTEGER NOT NULL DEFAULT 0`
- `summary_json TEXT`

Add a unique index on `(video_id, track_id)`.

### `summary_json` Shape

`summary_json` stores compact per-track summary data derived from sampled detections:

```json
{
  "class": "person",
  "best_confidence": 0.93,
  "best_bbox": [100.0, 40.0, 260.0, 390.0],
  "clothing": [
    {
      "prompt": "a person wearing a red shirt",
      "confidence": 0.67,
      "category": "top"
    }
  ]
}
```

This keeps the schema minimal while making the track result directly usable in search responses.

## Storage Path Cleanup

The codebase currently mixes package-local storage paths such as `skyeye/skyeye.db` and `skyeye/data/...` with repository-root artifacts such as `./skyeye.db` and `./data/...`.
This phase will standardize runtime storage on one repository-root base directory.

Recommended base paths:

- Database: `<repo-root>/skyeye.db`
- Videos: `<repo-root>/data/videos`
- Frames: `<repo-root>/data/frames`

All runtime path helpers should resolve from one shared root constant instead of recomputing sibling-relative paths independently inside each module.

## Backend Module Changes

### `skyeye/db.py`

Responsibilities after this change:

1. Resolve the canonical database path from the shared project root.
2. Create the new `tracks` table and unique index.
3. Preserve existing `videos` and `frames` table initialization.

### `skyeye/services/video_service.py`

Responsibilities after this change:

1. Resolve videos and frames directories from the shared project root.
2. Use `YOLO.track` with ByteTrack for continuous person tracking.
3. Reset tracker state for each video to prevent ID leakage across videos.
4. Build person detections with optional `track_id`.
5. Aggregate an in-memory track summary map for the current video.
6. Write sampled frames as before.
7. Write `tracks` summary rows at the end of processing.

The in-memory track summary map should track:

- `track_id`
- `start_timestamp`
- `end_timestamp`
- `sample_count`
- `best_frame_id`
- `best_confidence`
- `best_bbox`
- `best_clothing`

The best frame should be the sampled frame with the highest person detection confidence for that track.

### `skyeye/services/search_service.py`

Responsibilities after this change:

1. Keep query parsing as-is for clothing and color matching.
2. When a matched person detection includes `track_id`, group results by `(video_id, track_id)`.
3. Select one representative result per track, preferring the stored `tracks.best_frame_id` if available, otherwise the highest-confidence matched sampled frame.
4. Keep the old IoU-based frame deduplication fallback for results without `track_id`.

The search response should minimally add:

- `track_id` for tracked person results when available

The rest of the API contract should remain stable.

### `skyeye/services/image_service.py`

Responsibilities after this change:

1. When annotating a detection that has `track_id`, append `ID:{track_id}` to the label.
2. Keep existing highlighting behavior unchanged.

## Search Result Behavior

### Person Query

For person-related queries with matched tracked detections:

1. Collect all matching sampled detections from `frames`.
2. Split into tracked results and untracked results.
3. For tracked results, group by `(video_id, track_id)`.
4. For each group, choose one representative frame.
5. Return one result per track instead of many adjacent frames.

### Non-Person Query

For detections without `track_id`, keep the existing deduplication heuristic based on time gap and IoU.

This preserves current behavior for cars, dogs, cats, and other classes in this phase.

## API Compatibility

No new endpoint is required for this phase.

The existing `/api/search` response may include:

- `track_id`

The existing `/api/frames/{frame_id}/annotated` endpoint remains valid because annotated labels are derived from the stored detection payload.

## Error Handling

1. If tracking output has no IDs for a frame, that frame still stores detections without `track_id`.
2. If CLIP fails for a sampled person crop, store the detection with empty `clothing` and continue processing.
3. If track summary writing fails, the whole processing job should mark the video as `error` because track-level search depends on consistent summary data.
4. If a video contains no tracked persons, processing still succeeds and search falls back to frame-level behavior.

## Testing Strategy

This feature will be implemented with TDD.
The tests should focus on deterministic service-level behavior and avoid requiring heavy model inference in the test suite.

### Unit Test Targets

1. Database initialization creates the `tracks` table and unique index.
2. Search groups tracked person results by `(video_id, track_id)`.
3. Search falls back to old frame-level deduplication for untracked results.
4. Image annotation includes `ID:{track_id}` when present.
5. Track summary aggregation picks the highest-confidence sampled frame as the representative frame.

### Integration Boundaries

The code should be structured so tracker output and CLIP output can be stubbed in tests.
Tests should exercise our aggregation and selection logic, not Ultralytics internals.

## Migration and Rollout

1. Existing rows in `frames` remain valid because `track_id` is optional inside `detections_json`.
2. Existing videos do not automatically gain track summaries; only newly processed videos are guaranteed to have `tracks` rows.
3. If needed later, a backfill command can be added, but it is out of scope for this phase.

## Risks

1. Running tracking on every frame increases CPU or GPU processing time.
2. ByteTrack quality may still degrade on low-FPS or severe occlusion videos.
3. Keeping full detection payloads in JSON limits analytical querying, but that trade-off is acceptable for the current minimal scope.
4. Existing repository-root versus package-local path confusion can cause accidental reads from stale data if not fully standardized during implementation.

## Acceptance Criteria

1. A newly processed video stores `track_id` on sampled person detections when tracking data is available.
2. A newly processed video writes one `tracks` row per tracked person per video.
3. A person search returns one primary result per track instead of many adjacent frames from the same person.
4. Non-person searches continue to work.
5. Annotated frame labels show `ID:{track_id}` for tracked persons.
6. The backend uses one canonical runtime storage location for the database and data directories.
