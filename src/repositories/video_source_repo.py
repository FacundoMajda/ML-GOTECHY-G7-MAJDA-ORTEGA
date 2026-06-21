# src/repositories/video_source_repo.py
import json
from typing import Optional
from uuid import UUID

from src.models.contracts import ROIConfig, VideoSourceConfig
from src.models.enums import SourceType
from src.repositories.db import execute_query


class VideoSourceRepository:
    def create(self, config: VideoSourceConfig) -> UUID:
        row = execute_query(
            """
            INSERT INTO video_source (id, name, source_type, source_uri, is_live)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (config.id, config.name, config.source_type.value, config.source_uri, config.is_live),
            fetch="one",
        )
        return row[0]

    def get_by_id(self, video_id: str) -> Optional[VideoSourceConfig]:
        rows = execute_query(
            "SELECT id, name, source_type, source_uri, is_live FROM video_source WHERE id = %s",
            (video_id,),
            fetch="all",
        )
        if not rows:
            return None
        row = rows[0]
        return VideoSourceConfig(
            id=str(row[0]),
            name=row[1],
            source_type=SourceType(row[2]),
            source_uri=row[3],
            is_live=row[4],
        )

    def list_all(self) -> list[VideoSourceConfig]:
        rows = execute_query(
            "SELECT id, name, source_type, source_uri, is_live FROM video_source ORDER BY created_at DESC",
            fetch="all",
        )
        return [
            VideoSourceConfig(
                id=str(row[0]),
                name=row[1],
                source_type=SourceType(row[2]),
                source_uri=row[3],
                is_live=row[4],
            )
            for row in rows
        ]

    def delete(self, video_id: str) -> None:
        execute_query("DELETE FROM video_source WHERE id = %s", (video_id,), fetch=None)

    def create_roi(self, roi: ROIConfig, video_source_id: str) -> UUID:
        row = execute_query(
            """
            INSERT INTO roi (id, video_source_id, name, polygon, positive_label, negative_label,
                             detect_entry, detect_exit, detect_occupancy, detect_dwell, alerts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                roi.id,
                video_source_id,
                roi.name,
                json.dumps(roi.polygon),
                roi.positive_label,
                roi.negative_label,
                roi.detect_entry,
                roi.detect_exit,
                roi.detect_occupancy,
                roi.detect_dwell,
                json.dumps(roi.alerts),
            ),
            fetch="one",
        )
        return row[0]

    def get_all_with_rois(self) -> list[tuple[VideoSourceConfig, list[ROIConfig]]]:
        sources = self.list_all()
        return [(src, self.get_rois_for_source(src.id)) for src in sources]

    def get_rois_for_source(self, video_source_id: str) -> list[ROIConfig]:
        rows = execute_query(
            """
            SELECT id, name, polygon, positive_label, negative_label,
                   detect_entry, detect_exit, detect_occupancy, detect_dwell, alerts
            FROM roi WHERE video_source_id = %s
            """,
            (video_source_id,),
            fetch="all",
        )
        return [
            ROIConfig(
                id=str(row[0]),
                name=row[1],
                polygon=row[2] if isinstance(row[2], list) else json.loads(row[2]),
                positive_label=row[3],
                negative_label=row[4],
                detect_entry=row[5],
                detect_exit=row[6],
                detect_occupancy=row[7],
                detect_dwell=row[8],
                alerts=row[9] if isinstance(row[9], list) else json.loads(row[9]),
            )
            for row in rows
        ]

    def get_roi_by_id(self, roi_id: str) -> Optional[dict]:
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
            "id": str(row[0]),
            "name": row[1],
            "polygon": row[2] if isinstance(row[2], list) else json.loads(row[2]),
            "positive_label": row[3],
            "negative_label": row[4],
            "detect_entry": row[5],
            "detect_exit": row[6],
            "detect_occupancy": row[7],
            "detect_dwell": row[8],
            "alerts": row[9] if isinstance(row[9], list) else json.loads(row[9]),
            "video_source_id": str(row[10]),
        }

    def delete_roi(self, roi_id: str) -> None:
        execute_query("DELETE FROM roi WHERE id = %s", (roi_id,), fetch=None)

    def update_roi_config(self, roi_id: str, config: dict) -> None:
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
            tuple(params),
            fetch=None,
        )
