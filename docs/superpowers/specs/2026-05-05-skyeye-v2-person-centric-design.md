# SkyEye V2.1 Person-Centric Pipeline Design

## Summary

SkyEye V2.1 upgrades the system from frame-centric search to person-centric search.
The backend will treat a tracked person as the primary result entity, generate cropped person images and context images for the frontend, and introduce replaceable database, object storage, and feature extraction boundaries.

This version deliberately avoids requiring new heavyweight model downloads.
YOLO + ByteTrack and the existing CLIP path can continue to run while the new pipeline shape is introduced.
ReID, pedestrian attribute recognition, VLM extraction, PostgreSQL, pgvector, and MinIO are planned as later plug-ins behind stable interfaces.

## Goals

1. Return searchable people rather than only large scene frames.
2. Store each tracked person as a first-class entity.
3. Store per-track observations with crop and context image URIs.
4. Select representative observations for each tracked person.
5. Expose person detail and gallery APIs for the frontend.
6. Add storage and repository abstractions so SQLite/local files can later be replaced by PostgreSQL/pgvector/MinIO.
7. Keep the first implementation compatible with the existing upload and search flow.

## Non-Goals

1. Do not migrate to PostgreSQL in V2.1.
2. Do not require pgvector in V2.1.
3. Do not require MinIO in V2.1.
4. Do not add a new mandatory ReID/PAR/VLM model in V2.1.
5. Do not solve cross-video identity matching in V2.1.
6. Do not replace ByteTrack unless tracking quality forces a later V2.2 upgrade.

## User Experience

Search results should become person cards:

1. A large cropped image of the matched person.
2. A context image from the original frame.
3. The tracked person ID and timestamp range.
4. A compact feature summary.
5. A gallery of other cropped appearances for that person.

The current frame image can remain available, but it should no longer be the only visual evidence shown to the user.

## Backend Architecture

The backend should move toward these responsibility boundaries:

```text
api/
  videos.py              upload and video status
  search.py              search entry point
  persons.py             person detail and gallery APIs

domain/
  models.py              dataclasses for tracks, observations, and features

storage/
  object_store.py        object storage protocol
  local_store.py         filesystem-backed implementation

repositories/
  sqlite_repository.py   SQLite persistence implementation

pipeline/
  video_pipeline.py      orchestration
  representative.py      observation quality and representative selection
  cropper.py             crop and context image generation

features/
  base.py                feature extractor protocol
```

The current `skyeye.services.video_service.process_video` can remain as the compatibility entry point, but its internal responsibilities should be gradually moved behind these smaller units.

## Data Model

### Existing Tables

The current `videos`, `frames`, and `tracks` tables remain valid.
V2.1 adds normalized tables while keeping the current JSON payloads compatible.

### `person_tracks`

One row per tracked person inside one video.

- `id TEXT PRIMARY KEY`
- `video_id TEXT NOT NULL`
- `track_id INTEGER NOT NULL`
- `start_timestamp REAL NOT NULL`
- `end_timestamp REAL NOT NULL`
- `best_observation_id TEXT`
- `status TEXT NOT NULL DEFAULT 'ready'`
- `summary_json TEXT`

Unique index:

- `(video_id, track_id)`

### `track_observations`

One persisted observation for a tracked person on a sampled frame.

- `id TEXT PRIMARY KEY`
- `person_track_id TEXT NOT NULL`
- `frame_id TEXT NOT NULL`
- `video_id TEXT NOT NULL`
- `track_id INTEGER NOT NULL`
- `timestamp REAL NOT NULL`
- `bbox_json TEXT NOT NULL`
- `confidence REAL NOT NULL`
- `crop_uri TEXT`
- `context_uri TEXT`
- `quality_score REAL NOT NULL DEFAULT 0`
- `is_representative INTEGER NOT NULL DEFAULT 0`

Indexes:

- `(person_track_id, timestamp)`
- `(video_id, track_id)`

### `track_representatives`

Named representative observations for one tracked person.

- `id TEXT PRIMARY KEY`
- `person_track_id TEXT NOT NULL`
- `observation_id TEXT NOT NULL`
- `kind TEXT NOT NULL`
- `score REAL NOT NULL DEFAULT 0`

Unique index:

- `(person_track_id, kind)`

### `person_features`

Feature records produced by current or future extractors.

- `id TEXT PRIMARY KEY`
- `person_track_id TEXT NOT NULL`
- `observation_id TEXT`
- `extractor TEXT NOT NULL`
- `model_name TEXT NOT NULL`
- `model_version TEXT`
- `feature_type TEXT NOT NULL`
- `vector_json TEXT`
- `attributes_json TEXT`
- `text TEXT`
- `confidence REAL`
- `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

In SQLite, vectors can be serialized JSON.
In PostgreSQL + pgvector, repository code can map the same domain field to a vector column.

## File Storage

The pipeline should write through an object store interface.
Local storage is the V2.1 implementation.

Recommended local layout:

```text
data/
  videos/{video_id}/source{ext}
  frames/{video_id}/{frame_id}.jpg
  persons/{video_id}/{person_track_id}/crops/{observation_id}.jpg
  persons/{video_id}/{person_track_id}/contexts/{observation_id}.jpg
  persons/{video_id}/{person_track_id}/representatives/{kind}.jpg
```

The database stores URIs rather than assuming raw filesystem paths.
For local files, the URI may be `local://persons/...`.
For MinIO later, the same field can store `s3://skyeye/persons/...` or a bucket/key pair behind the repository.

## Representative Selection

V2.1 uses deterministic scoring that does not require new models:

1. Detection confidence.
2. Bounding-box area ratio.
3. Blur score from Laplacian variance.
4. Penalty when the box touches frame boundaries.
5. Mild diversity by keeping observations across time.

The first representative kind is `best`.
Future kinds can include `front`, `full_body`, and `sharpest`.

## Feature Extraction Boundary

Feature extractors should share this conceptual interface:

```text
extract(person crop, optional context, metadata) -> feature records
```

Initial V2.1 extractors:

1. `legacy_clip_clothing`: wraps current CLIP clothing output when available.
2. `metadata_summary`: stores simple detection and representative metadata.

Future extractors:

1. `reid_osnet`: identity similarity vector.
2. `pedestrian_attribute`: structured person attributes.
3. `vlm_description`: structured natural-language JSON.
4. `clip_embedding`: semantic vector retrieval.

## API Changes

### Search

`POST /api/search` should continue to work.
Tracked person results may include:

- `person_track_id`
- `track_id`
- `crop_url`
- `context_url`
- `gallery_preview`
- `features`
- `start_timestamp`
- `end_timestamp`

### Person Detail

Add:

```text
GET /api/persons/{person_track_id}
GET /api/persons/{person_track_id}/gallery
```

The detail response includes the best crop, context image, track metadata, features, and representative observations.

The gallery response returns observation images ordered by timestamp.

## Frontend Changes

The frontend should show person-centric results:

1. Large crop preview.
2. Context image beside or behind the crop.
3. Feature summary panel.
4. Gallery strip for other observations.
5. Stable track/person identifiers.

The frontend should remain tolerant of old search results that only contain `frame_id`.

## Error Handling

1. If crop generation fails for an observation, persist the observation with empty crop/context URIs and continue.
2. If representative selection has no observations for a track, the person track remains searchable through the old frame fallback.
3. If new normalized table writes fail, mark the video as `error` because person-centric search depends on consistent data.
4. Existing `frames.detections_json` remains the fallback compatibility store.

## Testing Strategy

V2.1 tests should not run YOLO, CLIP, or video inference.
They should test deterministic units:

1. Database initialization creates new V2.1 tables and indexes.
2. Object store maps URIs to local paths safely.
3. Cropper creates crop and context images from a synthetic frame.
4. Representative scoring prefers clear, large, non-boundary observations.
5. Search results include person-centric fields when normalized rows exist.
6. Person gallery API returns observations ordered by timestamp.

## Acceptance Criteria

1. Newly processed tracked persons have rows in `person_tracks`.
2. Sampled tracked detections have rows in `track_observations`.
3. Crop and context images are stored through the object store abstraction.
4. At least one best representative is selected per observed tracked person.
5. Search returns person-centric result fields for tracked results.
6. Frontend displays a cropped person image, context image, feature summary, and gallery preview when available.
7. Existing videos and frame-level fallback behavior remain usable.
