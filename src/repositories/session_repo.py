# src/repositories/session_repo.py
import json
import uuid
from datetime import datetime
from uuid import UUID

from src.models.contracts import SessionResult
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
            fetch=None,
        )
        print(f"[DEBUG] SessionRepository.create_session: returning uuid={session_uuid}", flush=True)
        return session_uuid

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


