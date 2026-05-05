# SkyEye V2.1 Person-Centric Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first person-centric SkyEye pipeline foundation with normalized person-track storage, local object storage abstraction, crop/context images, person gallery APIs, and frontend person cards.

**Architecture:** Keep the existing upload/search APIs compatible while adding V2.1 tables and services beside them. `process_video` remains the entry point, but deterministic helpers handle crop creation, representative scoring, and person-centric repository writes.

**Tech Stack:** Python 3.14, FastAPI, SQLite, OpenCV, Ultralytics, CLIP, React, TypeScript, Vite, uv, bun.

---

## File Structure

- Create: `skyeye/storage/object_store.py` for the storage protocol and URI helpers.
- Create: `skyeye/storage/local_store.py` for the local filesystem-backed object store.
- Create: `skyeye/pipeline/cropper.py` for crop/context image generation.
- Create: `skyeye/pipeline/representative.py` for deterministic observation scoring.
- Create: `skyeye/repositories/person_repository.py` for SQLite person-track persistence reads/writes.
- Create: `skyeye/api/persons.py` for person detail and gallery endpoints.
- Modify: `skyeye/db.py` to create V2.1 tables and indexes.
- Modify: `skyeye/services/video_service.py` to write V2.1 person rows during existing processing.
- Modify: `skyeye/services/search_service.py` to enrich tracked results with person-centric fields.
- Modify: `skyeye/api/__init__.py` and `skyeye/main.py` to register person APIs.
- Modify: `web/src/types.ts`, `web/src/lib/api.ts`, `web/src/components/ResultCard.tsx`, and search UI components for crop/gallery/feature display.
- Test: Add backend tests under `tests/` and frontend checks through existing package scripts.

## Task 1: Database Schema

**Files:**
- Modify: `skyeye/db.py`
- Test: `tests/test_db_paths.py`

- [ ] **Step 1: Write failing schema test**

Add assertions that `person_tracks`, `track_observations`, `track_representatives`, and `person_features` exist after `init_db()`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest tests.test_db_paths -v`

Expected: FAIL because V2.1 tables do not exist.

- [ ] **Step 3: Implement schema**

Add `CREATE TABLE IF NOT EXISTS` statements and indexes in `skyeye/db.py`.

- [ ] **Step 4: Run schema test**

Run: `uv run python -m unittest tests.test_db_paths -v`

Expected: PASS.

## Task 2: Local Object Store

**Files:**
- Create: `skyeye/storage/__init__.py`
- Create: `skyeye/storage/object_store.py`
- Create: `skyeye/storage/local_store.py`
- Test: `tests/test_object_store.py`

- [ ] **Step 1: Write failing local store test**

Test that `LocalObjectStore.put_bytes("persons/a.jpg", b"x", "image/jpeg")` returns a `local://persons/a.jpg` URI and writes the file under the configured root.

- [ ] **Step 2: Verify red**

Run: `uv run python -m unittest tests.test_object_store -v`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement minimal local store**

Implement safe relative-key storage with `put_bytes`, `resolve_uri`, and `delete`.

- [ ] **Step 4: Verify green**

Run: `uv run python -m unittest tests.test_object_store -v`

Expected: PASS.

## Task 3: Cropper and Representative Scoring

**Files:**
- Create: `skyeye/pipeline/__init__.py`
- Create: `skyeye/pipeline/cropper.py`
- Create: `skyeye/pipeline/representative.py`
- Test: `tests/test_person_pipeline.py`

- [ ] **Step 1: Write failing cropper test**

Use a synthetic NumPy image and bbox. Assert that crop bytes and context bytes are valid JPEGs and crop dimensions are smaller than frame dimensions.

- [ ] **Step 2: Write failing scoring test**

Assert that a centered large bbox with high confidence scores higher than a tiny boundary-touching bbox.

- [ ] **Step 3: Verify red**

Run: `uv run python -m unittest tests.test_person_pipeline -v`

Expected: FAIL because modules do not exist.

- [ ] **Step 4: Implement cropper and scoring**

Use OpenCV `imencode(".jpg", image)` and deterministic quality scoring.

- [ ] **Step 5: Verify green**

Run: `uv run python -m unittest tests.test_person_pipeline -v`

Expected: PASS.

## Task 4: Person Repository

**Files:**
- Create: `skyeye/repositories/__init__.py`
- Create: `skyeye/repositories/person_repository.py`
- Test: `tests/test_person_repository.py`

- [ ] **Step 1: Write failing repository test**

Create an in-memory/temp SQLite database through `init_db()`, insert a video/frame, upsert a person track and observation, then fetch detail and gallery ordered by timestamp.

- [ ] **Step 2: Verify red**

Run: `uv run python -m unittest tests.test_person_repository -v`

Expected: FAIL because repository does not exist.

- [ ] **Step 3: Implement repository methods**

Implement `upsert_person_track`, `insert_observation`, `set_best_observation`, `get_person_detail`, `get_person_gallery`, and `get_person_search_index`.

- [ ] **Step 4: Verify green**

Run: `uv run python -m unittest tests.test_person_repository -v`

Expected: PASS.

## Task 5: Integrate Person Writes in Video Processing

**Files:**
- Modify: `skyeye/services/video_service.py`
- Test: `tests/test_video_service.py`

- [ ] **Step 1: Write failing unit test for person write payloads**

Test deterministic helper behavior without running YOLO: given tracked sampled detections and frame metadata, build person track and observation payloads with crop keys and quality scores.

- [ ] **Step 2: Verify red**

Run: `uv run python -m unittest tests.test_video_service -v`

Expected: FAIL because helper is missing.

- [ ] **Step 3: Implement helper and call it from `process_video`**

Generate crops/contexts only for sampled tracked person detections. Store rows through `PersonRepository`.

- [ ] **Step 4: Verify green**

Run: `uv run python -m unittest tests.test_video_service -v`

Expected: PASS.

## Task 6: Search Enrichment and Person APIs

**Files:**
- Create: `skyeye/api/persons.py`
- Modify: `skyeye/api/__init__.py`
- Modify: `skyeye/main.py`
- Modify: `skyeye/services/search_service.py`
- Test: `tests/test_search_service.py`
- Test: `tests/test_person_api.py`

- [ ] **Step 1: Write failing search enrichment test**

Assert that `group_tracked_results` or search enrichment returns `person_track_id`, `crop_uri`, `context_uri`, and timestamp range when a matching track exists.

- [ ] **Step 2: Write failing API test**

Use FastAPI `TestClient` to call `/api/persons/{person_track_id}/gallery` and assert ordered observations.

- [ ] **Step 3: Verify red**

Run: `uv run python -m unittest tests.test_search_service tests.test_person_api -v`

Expected: FAIL.

- [ ] **Step 4: Implement enrichment and APIs**

Add repository reads to search output and register person router.

- [ ] **Step 5: Verify green**

Run: `uv run python -m unittest tests.test_search_service tests.test_person_api -v`

Expected: PASS.

## Task 7: Frontend Person Cards

**Files:**
- Modify: `web/src/types.ts`
- Modify: `web/src/lib/api.ts`
- Modify: `web/src/components/ResultCard.tsx`
- Modify: `web/src/components/SearchResultsPanel.tsx`

- [ ] **Step 1: Update TypeScript types**

Add optional `person_track_id`, `crop_url`, `context_url`, `gallery_preview`, `features`, `start_timestamp`, and `end_timestamp` fields.

- [ ] **Step 2: Update result card rendering**

Prefer crop image when available, show context image as secondary visual, display track/person ID, feature chips, and a gallery strip.

- [ ] **Step 3: Run frontend checks**

Run: `cd web; bun run lint`

Expected: PASS.

## Task 8: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run backend tests**

Run: `uv run python -m unittest discover -v`

Expected: PASS.

- [ ] **Step 2: Run frontend checks**

Run: `cd web; bun run lint`

Expected: PASS.

- [ ] **Step 3: Manual smoke path**

Run backend with `uv run python -m skyeye.main`, upload a short video, search for `person`, and confirm results include person-centric fields when tracks are available.

## Scope Notes

- New model downloads are not required for V2.1.
- ReID/PAR/VLM are intentionally deferred until the person-centric data and UI path is stable.
- If CLIP model download blocks local processing, V2.1 should still support crop/gallery generation and metadata summaries.
