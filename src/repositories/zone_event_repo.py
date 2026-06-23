# src/repositories/zone_event_repo.py
import json
import uuid
from uuid import UUID

from src.models.contracts import ZoneEventRecord
from src.repositories.db import execute_query


class ZoneEventRepository:
    def create(self, session_id: UUID, event: ZoneEventRecord) -> None:
        print(f"[DEBUG] ZoneEventRepository.create: ENTRY session_id={session_id} roi_id={event.roi_id} type={event.event_type.value}", flush=True)
        execute_query(
            """
            INSERT INTO zone_event
            (id, session_id, roi_id, track_id, event_type, occurred_at, frame_number, dwell_seconds, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), str(session_id), event.roi_id, event.track_id,
             event.event_type.value, event.occurred_at, event.frame_number,
             event.dwell_seconds, json.dumps(event.metadata)),
            fetch=None,
        )

    def get_dwell_times(self) -> list[dict]:
        print(f"[DEBUG] ZoneEventRepository.get_dwell_times: ENTRY", flush=True)
        rows = execute_query(
            """
            SELECT ze.roi_id, r.name AS roi_name,
                   AVG(ze.dwell_seconds)::numeric(10,2) AS avg_dwell_seconds,
                   MAX(ze.dwell_seconds)::numeric(10,2) AS max_dwell_seconds,
                   COUNT(*) AS exit_count
            FROM zone_event ze
            JOIN roi r ON ze.roi_id = r.id
            WHERE ze.event_type = 'exit' AND ze.dwell_seconds IS NOT NULL
            GROUP BY ze.roi_id, r.name
            ORDER BY avg_dwell_seconds DESC
            """,
            fetch="all",
        )
        return [
            {
                "roi_id": str(row[0]), "roi_name": row[1],
                "avg_dwell_seconds": float(row[2]) if row[2] is not None else 0,
                "max_dwell_seconds": float(row[3]) if row[3] is not None else 0,
                "exit_count": int(row[4]) if row[4] is not None else 0,
            }
            for row in rows
        ]

    def get_by_session(self, session_id: UUID) -> list:
        rows = execute_query(
            """
            SELECT id, session_id, roi_id, track_id, event_type,
                   occurred_at, frame_number, dwell_seconds, metadata
            FROM zone_event
            WHERE session_id = %s
            ORDER BY occurred_at
            """,
            (str(session_id),),
            fetch="all",
        )
        return [
            {
                "id": r[0], "session_id": r[1], "roi_id": r[2],
                "track_id": r[3], "event_type": r[4],
                "occurred_at": r[5], "frame_number": r[6],
                "dwell_seconds": r[7], "metadata": json.loads(r[8]) if r[8] else {},
            }
            for r in rows
        ]
