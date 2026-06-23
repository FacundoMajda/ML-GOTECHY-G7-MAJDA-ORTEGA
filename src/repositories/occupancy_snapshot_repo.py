# src/repositories/occupancy_snapshot_repo.py
from uuid import UUID

from src.models.contracts import OccupancySnapshot
from src.repositories.db import execute_batch, execute_query


class OccupancySnapshotRepository:
    def create_batch(self, session_id: UUID, snapshots: list[OccupancySnapshot]) -> None:
        if not snapshots:
            print("[DEBUG] OccupancySnapshotRepository.create_batch: 0 snapshots, skip", flush=True)
            return
        params_list = [
            (str(session_id), snap.roi_id, snap.captured_at,
             snap.frame_number, snap.count_inside, snap.count_outside, snap.track_ids_inside)
            for snap in snapshots
        ]
        print(f"[DEBUG] OccupancySnapshotRepository.create_batch: batch insert n={len(params_list)}", flush=True)
        execute_batch(
            """
            INSERT INTO roi_occupancy_snapshot
            (session_id, roi_id, captured_at, frame_number, count_inside, count_outside, track_ids_inside)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id, roi_id, frame_number) DO NOTHING
            """,
            params_list,
        )

    def get_occupancy_trends(self) -> list[dict]:
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
