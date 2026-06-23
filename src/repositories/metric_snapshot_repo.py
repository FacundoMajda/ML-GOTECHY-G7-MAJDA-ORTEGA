import uuid
from datetime import datetime, timezone
from typing import Optional
from src.repositories.db import get_db_pool


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
        pool = get_db_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO metric_snapshot
                        (session_id, roi_id, entries, exits, max_occupancy, avg_dwell_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (session_id, roi_id, entries, exits, max_occupancy, avg_dwell_seconds),
                )
                row = cur.fetchone()
                conn.commit()
                return row[0]

    def get_by_session(self, session_id: uuid.UUID) -> list:
        pool = get_db_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, roi_id, entries, exits,
                           max_occupancy, avg_dwell_seconds, computed_at
                    FROM metric_snapshot
                    WHERE session_id = %s
                    ORDER BY computed_at
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "session_id": r[1],
                        "roi_id": r[2],
                        "entries": r[3],
                        "exits": r[4],
                        "max_occupancy": r[5],
                        "avg_dwell_seconds": r[6],
                        "computed_at": r[7],
                    }
                    for r in rows
                ]

    def delete_by_session(self, session_id: uuid.UUID) -> int:
        pool = get_db_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM metric_snapshot WHERE session_id = %s RETURNING id",
                    (session_id,),
                )
                count = cur.rowcount
                conn.commit()
                return count
