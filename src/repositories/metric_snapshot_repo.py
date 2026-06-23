import uuid
from typing import Optional
from src.repositories.db import execute_query


class MetricSnapshotRepository:
    """Repository for metric_snapshot table.

    MetricSnapshot is derived data — always recomputable from ZoneEvents.
    This repo handles persistence only, no business logic.

    Multi-class: one row per (session, roi, object_class). Use the
    `object_class` filter to query a specific class.
    """

    def save(
        self,
        session_id: uuid.UUID,
        roi_id: uuid.UUID,
        entries: int,
        exits: int,
        max_occupancy: int,
        object_class: str = "person",
        avg_dwell_seconds: Optional[float] = None,
        median_dwell_seconds: Optional[float] = None,
        unique_objects: int = 0,
    ) -> uuid.UUID:
        rows = execute_query(
            """
            INSERT INTO metric_snapshot
                (session_id, roi_id, object_class, entries, exits,
                 max_occupancy, avg_dwell_seconds, median_dwell_seconds, unique_objects)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id, roi_id, object_class) DO UPDATE
            SET entries = EXCLUDED.entries,
                exits = EXCLUDED.exits,
                max_occupancy = EXCLUDED.max_occupancy,
                avg_dwell_seconds = EXCLUDED.avg_dwell_seconds,
                median_dwell_seconds = EXCLUDED.median_dwell_seconds,
                unique_objects = EXCLUDED.unique_objects
            RETURNING id
            """,
            (str(session_id), str(roi_id), object_class,
             entries, exits, max_occupancy,
             avg_dwell_seconds, median_dwell_seconds, unique_objects),
            fetch="one",
        )
        return rows[0] if rows else None

    def get_by_session(self, session_id: uuid.UUID, object_class: Optional[str] = None) -> list:
        if object_class is None:
            rows = execute_query(
                """
                SELECT id, session_id, roi_id, object_class, entries, exits,
                       max_occupancy, avg_dwell_seconds, median_dwell_seconds,
                       unique_objects, computed_at
                FROM metric_snapshot
                WHERE session_id = %s
                ORDER BY object_class, computed_at
                """,
                (str(session_id),),
                fetch="all",
            )
        else:
            rows = execute_query(
                """
                SELECT id, session_id, roi_id, object_class, entries, exits,
                       max_occupancy, avg_dwell_seconds, median_dwell_seconds,
                       unique_objects, computed_at
                FROM metric_snapshot
                WHERE session_id = %s AND object_class = %s
                ORDER BY computed_at
                """,
                (str(session_id), object_class),
                fetch="all",
            )
        if not rows:
            return []
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "roi_id": r[2],
                "object_class": r[3],
                "entries": r[4],
                "exits": r[5],
                "max_occupancy": r[6],
                "avg_dwell_seconds": float(r[7]) if r[7] is not None else None,
                "median_dwell_seconds": float(r[8]) if r[8] is not None else None,
                "unique_objects": r[9],
                "computed_at": r[10],
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
