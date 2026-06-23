# src/repositories/occupancy_snapshot_repo.py
from uuid import UUID

from src.models.contracts import OccupancySnapshot
from src.repositories.db import execute_query


class OccupancySnapshotRepository:
    def create(self, session_id: UUID, snapshot: OccupancySnapshot) -> None:
        print(f"[DEBUG] OccupancySnapshotRepository.create: ENTRY session_id={session_id} roi_id={snapshot.roi_id}", flush=True)
        execute_query(
            """
            INSERT INTO roi_occupancy_snapshot
            (session_id, roi_id, captured_at, frame_number, count_inside, count_outside, track_ids_inside)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (str(session_id), snapshot.roi_id, snapshot.captured_at,
             snapshot.frame_number, snapshot.count_inside,
             snapshot.count_outside, snapshot.track_ids_inside),
            fetch=None,
        )

    def get_occupancy_trends(self) -> list[dict]:
        print(f"[DEBUG] OccupancySnapshotRepository.get_occupancy_trends: ENTRY", flush=True)
        rows = execute_query(
            """
            SELECT date_trunc('hour', captured_at) AS hour,
                   AVG(count_inside)::int AS avg_occupancy,
                   MAX(count_inside) AS peak_occupancy
            FROM roi_occupancy_snapshot
            WHERE captured_at >= NOW() - INTERVAL '24 hours'
            GROUP BY date_trunc('hour', captured_at)
            ORDER BY hour
            """,
            fetch="all",
        )
        return [
            {
                "hour": row[0].isoformat() if row[0] else row[0],
                "avg_occupancy": int(row[1]) if row[1] is not None else 0,
                "peak_occupancy": int(row[2]) if row[2] is not None else 0,
            }
            for row in rows
        ]
