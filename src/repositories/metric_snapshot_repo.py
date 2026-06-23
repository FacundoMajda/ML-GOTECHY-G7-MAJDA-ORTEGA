import uuid
from typing import Optional
from src.repositories.db import execute_query


class MetricSnapshotRepository:
    """Repository for metric_snapshot table.

    MetricSnapshot is derived data — always recomputable from ZoneEvents.
    This repo handles persistence only, no business logic.
    """

    def save(
        self,
        session_id: uuid.UUID,
        roi_id: uuid.UUID,
        entries: int,
        exits: int,
        max_occupancy: int,
        avg_dwell_seconds: Optional[float] = None,
    ) -> uuid.UUID:
        rows = execute_query(
            """
            INSERT INTO metric_snapshot
                (session_id, roi_id, entries, exits, max_occupancy, avg_dwell_seconds)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (str(session_id), str(roi_id), entries, exits, max_occupancy, avg_dwell_seconds),
            fetch="one",
        )
        return rows[0] if rows else None

    def get_by_session(self, session_id: uuid.UUID) -> list:
        rows = execute_query(
            """
            SELECT id, session_id, roi_id, entries, exits,
                   max_occupancy, avg_dwell_seconds, computed_at
            FROM metric_snapshot
            WHERE session_id = %s
            ORDER BY computed_at
            """,
            (str(session_id),),
            fetch="all",
        )
        if not rows:
            return []
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "roi_id": r[2],
                "entries": r[3],
                "exits": r[4],
                "max_occupancy": r[5],
                "avg_dwell_seconds": float(r[6]) if r[6] is not None else None,
                "computed_at": r[7],
            }
            for r in rows
        ]

    def delete_by_session(self, session_id: uuid.UUID) -> int:
        rows = execute_query(
            "DELETE FROM metric_snapshot WHERE session_id = %s RETURNING id",
            (str(session_id),),
            fetch="all",
        )
        return len(rows) if rows else 0
