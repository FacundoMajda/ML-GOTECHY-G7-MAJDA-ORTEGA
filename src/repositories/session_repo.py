# src/repositories/session_repo.py
import json
import uuid
from datetime import datetime
from uuid import UUID

from src.models.contracts import (
    OccupancySnapshot,
    SessionResult,
    TrackedEntityRecord,
    ZoneEventRecord,
)
from src.models.enums import TimestampMode
from src.repositories.db import execute_query


class SessionRepository:
    def create_session(self, session: SessionResult) -> UUID:
        print(f"[DEBUG] SessionRepository.create_session: ENTRY video_source_id={session.video_source_id}", flush=True)
        session_uuid = uuid.uuid4()
        execute_query(
            """
            INSERT INTO detection_session (
                id, video_source_id, started_at, ended_at, timestamp_mode,
                fps, total_frames, write_video, output_video_path, extra_analysis
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(session_uuid),
                session.video_source_id,
                session.started_at,
                session.ended_at,
                session.timestamp_mode.value,
                session.fps,
                session.total_frames,
                session.write_video,
                session.output_video_path,
                json.dumps(session.extra_analysis) if session.extra_analysis else None,
            ),
        )
        print(f"[DEBUG] SessionRepository.create_session: returning uuid={session_uuid}", flush=True)
        return session_uuid

    def save_tracked_entities(
        self, session_id: UUID, entities: list[TrackedEntityRecord]
    ) -> None:
        print(f"[DEBUG] SessionRepository.save_tracked_entities: ENTRY session_id={session_id} n_entities={len(entities)}", flush=True)
        for e in entities:
            execute_query(
                """
                INSERT INTO tracked_entity
                (id, session_id, track_id, first_seen_at, last_seen_at, first_seen_frame, last_seen_frame)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id, track_id) DO UPDATE
                SET last_seen_at = EXCLUDED.last_seen_at,
                    last_seen_frame = EXCLUDED.last_seen_frame
                """,
                (
                    str(uuid.uuid4()),
                    str(session_id),
                    e.track_id,
                    e.first_seen_at,
                    e.last_seen_at,
                    e.first_seen_frame,
                    e.last_seen_frame,
                ),
            )

    def save_occupancy_snapshot(
        self, session_id: UUID, snapshot: OccupancySnapshot
    ) -> None:
        print(f"[DEBUG] SessionRepository.save_occupancy_snapshot: ENTRY session_id={session_id} roi_id={snapshot.roi_id}", flush=True)
        execute_query(
            """
            INSERT INTO roi_occupancy_snapshot
            (session_id, roi_id, captured_at, frame_number, count_inside, count_outside, track_ids_inside)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(session_id),
                snapshot.roi_id,
                snapshot.captured_at,
                snapshot.frame_number,
                snapshot.count_inside,
                snapshot.count_outside,
                snapshot.track_ids_inside,
            ),
        )

    def save_zone_event(self, session_id: UUID, event: ZoneEventRecord) -> None:
        print(f"[DEBUG] SessionRepository.save_zone_event: ENTRY session_id={session_id} roi_id={event.roi_id} type={event.event_type.value}", flush=True)
        execute_query(
            """
            INSERT INTO zone_event
            (id, session_id, roi_id, track_id, event_type, occurred_at, frame_number, dwell_seconds, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                str(session_id),
                event.roi_id,
                event.track_id,
                event.event_type.value,
                event.occurred_at,
                event.frame_number,
                event.dwell_seconds,
                json.dumps(event.metadata),
            ),
        )

    def save_session_result(self, session: SessionResult) -> UUID:
        print(f"[DEBUG] SessionRepository.save_session_result: ENTRY session.id={session.id}", flush=True)
        session_id = self.create_session(session)
        if session.tracked_entities:
            self.save_tracked_entities(session_id, session.tracked_entities)
        for snap in session.occupancy_snapshots:
            self.save_occupancy_snapshot(session_id, snap)
        for ev in session.zone_events:
            self.save_zone_event(session_id, ev)
        print(f"[DEBUG] SessionRepository.save_session_result: returning {session_id}", flush=True)
        return session_id

    def list_all(self) -> list[dict]:
        print(f"[DEBUG] SessionRepository.list_all: ENTRY", flush=True)
        rows = execute_query(
            """
            SELECT
                ds.id,
                vs.name AS source_name,
                vs.source_type AS source_type,
                ds.started_at,
                ds.ended_at,
                EXTRACT(EPOCH FROM (ds.ended_at - ds.started_at)) AS duration_seconds,
                COALESCE(te.entity_count, 0) AS total_entities,
                COALESCE(ze.event_count, 0) AS total_events
            FROM detection_session ds
            LEFT JOIN video_source vs ON ds.video_source_id = vs.id
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS entity_count
                FROM tracked_entity
                GROUP BY session_id
            ) te ON ds.id = te.session_id
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS event_count
                FROM zone_event
                GROUP BY session_id
            ) ze ON ds.id = ze.session_id
            ORDER BY ds.started_at DESC
            """,
            fetch="all",
        )
        result = [
            {
                "id": str(row[0]),
                "source_name": row[1],
                "source_type": row[2],
                "started_at": row[3].isoformat() if row[3] else None,
                "ended_at": row[4].isoformat() if row[4] else None,
                "duration_seconds": float(row[5]) if row[5] is not None else None,
                "total_entities": int(row[6]),
                "total_events": int(row[7]),
                "status": "running" if row[4] is None else "completed",
            }
            for row in rows
        ]
        print(f"[DEBUG] SessionRepository.list_all: returning {len(result)} rows", flush=True)
        return result

    def get_by_id(self, session_id: str) -> dict | None:
        print(f"[DEBUG] SessionRepository.get_by_id: ENTRY session_id={session_id}", flush=True)
        rows = execute_query(
            """
            SELECT
                ds.id,
                vs.name AS source_name,
                vs.source_type AS source_type,
                ds.started_at,
                ds.ended_at,
                EXTRACT(EPOCH FROM (ds.ended_at - ds.started_at)) AS duration_seconds,
                COALESCE(te.entity_count, 0) AS total_entities,
                COALESCE(ze.event_count, 0) AS total_events
            FROM detection_session ds
            LEFT JOIN video_source vs ON ds.video_source_id = vs.id
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS entity_count
                FROM tracked_entity
                GROUP BY session_id
            ) te ON ds.id = te.session_id
            LEFT JOIN (
                SELECT session_id, COUNT(*) AS event_count
                FROM zone_event
                GROUP BY session_id
            ) ze ON ds.id = ze.session_id
            WHERE ds.id = %s
            ORDER BY ds.started_at DESC
            """,
            (session_id,),
            fetch="all",
        )
        if not rows:
            print(f"[DEBUG] SessionRepository.get_by_id: not found, returning None", flush=True)
            return None
        row = rows[0]
        result = {
            "id": str(row[0]),
            "source_name": row[1],
            "source_type": row[2],
            "started_at": row[3].isoformat() if row[3] else None,
            "ended_at": row[4].isoformat() if row[4] else None,
            "duration_seconds": float(row[5]) if row[5] is not None else None,
            "total_entities": int(row[6]),
            "total_events": int(row[7]),
        }
        print(f"[DEBUG] SessionRepository.get_by_id: returning {result}", flush=True)
        return result
