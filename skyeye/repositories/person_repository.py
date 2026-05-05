import json
import uuid

from skyeye.db import get_db_connection


class PersonRepository:
    """SQLite repository for person-centric V2.1 data."""

    def upsert_person_track(
        self,
        video_id: str,
        track_id: int,
        start_timestamp: float,
        end_timestamp: float,
        summary: dict | None = None,
    ) -> str:
        existing = self.get_person_track_id(video_id, track_id)
        person_track_id = existing or str(uuid.uuid4())
        summary_json = json.dumps(summary or {})

        conn = get_db_connection()
        cursor = conn.cursor()
        if existing:
            cursor.execute("""
                UPDATE person_tracks
                SET start_timestamp = MIN(start_timestamp, ?),
                    end_timestamp = MAX(end_timestamp, ?),
                    summary_json = ?
                WHERE id = ?
            """, (start_timestamp, end_timestamp, summary_json, person_track_id))
        else:
            cursor.execute("""
                INSERT INTO person_tracks (
                    id, video_id, track_id, start_timestamp, end_timestamp, status, summary_json
                ) VALUES (?, ?, ?, ?, ?, 'ready', ?)
            """, (person_track_id, video_id, track_id, start_timestamp, end_timestamp, summary_json))
        conn.commit()
        conn.close()
        return person_track_id

    def get_person_track_id(self, video_id: str, track_id: int) -> str | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM person_tracks WHERE video_id = ? AND track_id = ?
        """, (video_id, track_id))
        row = cursor.fetchone()
        conn.close()
        return row["id"] if row else None

    def insert_observation(
        self,
        person_track_id: str,
        frame_id: str,
        video_id: str,
        track_id: int,
        timestamp: float,
        bbox: list[float],
        confidence: float,
        crop_uri: str | None,
        context_uri: str | None,
        quality_score: float,
        is_representative: bool,
        observation_id: str | None = None,
    ) -> str:
        observation_id = observation_id or str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO track_observations (
                id, person_track_id, frame_id, video_id, track_id, timestamp, bbox_json,
                confidence, crop_uri, context_uri, quality_score, is_representative
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            observation_id,
            person_track_id,
            frame_id,
            video_id,
            track_id,
            timestamp,
            json.dumps(bbox),
            confidence,
            crop_uri,
            context_uri,
            quality_score,
            1 if is_representative else 0,
        ))
        conn.commit()
        conn.close()
        return observation_id

    def set_best_observation(self, person_track_id: str, observation_id: str, score: float) -> None:
        representative_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE person_tracks SET best_observation_id = ? WHERE id = ?
        """, (observation_id, person_track_id))
        cursor.execute("""
            INSERT INTO track_representatives (id, person_track_id, observation_id, kind, score)
            VALUES (?, ?, ?, 'best', ?)
            ON CONFLICT(person_track_id, kind)
            DO UPDATE SET observation_id = excluded.observation_id, score = excluded.score
        """, (representative_id, person_track_id, observation_id, score))
        cursor.execute("""
            UPDATE track_observations
            SET is_representative = CASE WHEN id = ? THEN 1 ELSE is_representative END
            WHERE person_track_id = ?
        """, (observation_id, person_track_id))
        conn.commit()
        conn.close()

    def get_person_detail(self, person_track_id: str) -> dict | None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, video_id, track_id, start_timestamp, end_timestamp,
                   best_observation_id, status, summary_json
            FROM person_tracks
            WHERE id = ?
        """, (person_track_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        result = dict(row)
        result["summary"] = json.loads(result.pop("summary_json") or "{}")
        return result

    def get_person_gallery(self, person_track_id: str) -> list[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, person_track_id, frame_id, video_id, track_id, timestamp, bbox_json,
                   confidence, crop_uri, context_uri, quality_score, is_representative
            FROM track_observations
            WHERE person_track_id = ?
            ORDER BY timestamp ASC
        """, (person_track_id,))
        rows = cursor.fetchall()
        conn.close()

        gallery = []
        for row in rows:
            item = dict(row)
            item["bbox"] = json.loads(item.pop("bbox_json"))
            item["is_representative"] = bool(item["is_representative"])
            gallery.append(item)
        return gallery

    def get_person_search_index(self, video_ids: list[str]) -> dict[tuple[str, int], dict]:
        if not video_ids:
            return {}

        placeholders = ",".join("?" * len(video_ids))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT
                pt.id AS person_track_id,
                pt.video_id,
                pt.track_id,
                pt.start_timestamp,
                pt.end_timestamp,
                pt.summary_json,
                obs.crop_uri,
                obs.context_uri
            FROM person_tracks pt
            LEFT JOIN track_observations obs ON obs.id = pt.best_observation_id
            WHERE pt.video_id IN ({placeholders})
        """, video_ids)
        rows = cursor.fetchall()
        conn.close()

        index = {}
        for row in rows:
            item = dict(row)
            item["summary"] = json.loads(item.pop("summary_json") or "{}")
            index[(item["video_id"], item["track_id"])] = item
        return index
