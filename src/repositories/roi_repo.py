# src/repositories/roi_repo.py
import json
from typing import Optional
from uuid import UUID

from src.models.contracts import ROIConfig
from src.repositories.db import execute_query


class ROIRepository:
    def create(self, roi: ROIConfig, video_source_id: str) -> UUID:
        print(f"[DEBUG] ROIRepository.create: ENTRY roi_id={roi.id} name={roi.name} source_id={video_source_id}", flush=True)
        row = execute_query(
            """
            INSERT INTO roi (id, video_source_id, name, polygon, positive_label, negative_label,
                             detect_entry, detect_exit, detect_occupancy, detect_dwell, alerts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                roi.id, video_source_id, roi.name,
                json.dumps(roi.polygon), roi.positive_label, roi.negative_label,
                roi.detect_entry, roi.detect_exit, roi.detect_occupancy, roi.detect_dwell,
                json.dumps(roi.alerts),
            ),
            fetch="one",
        )
        return row[0]

    def list_by_source(self, video_source_id: str) -> list[ROIConfig]:
        print(f"[DEBUG] ROIRepository.list_by_source: ENTRY source_id={video_source_id}", flush=True)
        rows = execute_query(
            """
            SELECT id, name, polygon, positive_label, negative_label,
                   detect_entry, detect_exit, detect_occupancy, detect_dwell, alerts
            FROM roi WHERE video_source_id = %s
            """,
            (video_source_id,),
            fetch="all",
        )
        result = [
            ROIConfig(
                id=str(row[0]), name=row[1],
                polygon=row[2] if isinstance(row[2], list) else json.loads(row[2]),
                positive_label=row[3], negative_label=row[4],
                detect_entry=row[5], detect_exit=row[6],
                detect_occupancy=row[7], detect_dwell=row[8],
                alerts=row[9] if isinstance(row[9], list) else json.loads(row[9]),
            )
            for row in rows
        ]
        return result

    def get_by_id(self, roi_id: str) -> Optional[dict]:
        print(f"[DEBUG] ROIRepository.get_by_id: ENTRY roi_id={roi_id}", flush=True)
        rows = execute_query(
            """
            SELECT id, name, polygon, positive_label, negative_label,
                   detect_entry, detect_exit, detect_occupancy, detect_dwell, alerts,
                   video_source_id
            FROM roi WHERE id = %s
            """,
            (roi_id,),
            fetch="all",
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "id": str(row[0]), "name": row[1],
            "polygon": row[2] if isinstance(row[2], list) else json.loads(row[2]),
            "positive_label": row[3], "negative_label": row[4],
            "detect_entry": row[5], "detect_exit": row[6],
            "detect_occupancy": row[7], "detect_dwell": row[8],
            "alerts": row[9] if isinstance(row[9], list) else json.loads(row[9]),
            "video_source_id": str(row[10]),
        }

    def delete(self, roi_id: str) -> None:
        print(f"[DEBUG] ROIRepository.delete: ENTRY roi_id={roi_id}", flush=True)
        execute_query("DELETE FROM roi WHERE id = %s", (roi_id,), fetch=None)

    def update_config(self, roi_id: str, config: dict) -> None:
        print(f"[DEBUG] ROIRepository.update_config: ENTRY roi_id={roi_id}", flush=True)
        allowed = {"detect_entry", "detect_exit", "detect_occupancy", "detect_dwell", "alerts"}
        updates = {k: v for k, v in config.items() if k in allowed}
        if not updates:
            return
        set_parts = []
        params = []
        for key in ("detect_entry", "detect_exit", "detect_occupancy", "detect_dwell"):
            if key in updates:
                set_parts.append(f"{key} = %s")
                params.append(updates[key])
        if "alerts" in updates:
            set_parts.append("alerts = %s")
            params.append(json.dumps(updates["alerts"]))
        if not set_parts:
            return
        params.append(roi_id)
        execute_query(
            f"UPDATE roi SET {', '.join(set_parts)} WHERE id = %s",
            tuple(params), fetch=None,
        )
