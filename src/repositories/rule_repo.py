# src/repositories/rule_repo.py
import json
from uuid import UUID

from src.repositories.db import execute_query


class RuleRepository:
    """Repository for roi_event_rule — alert/event rules per ROI.

    Each rule has:
    - event_type: what kind of event it emits (entry/exit/overcapacity/dwell_exceeded,
      plus the horizontal catalog: presence, occupancy_low, object_appeared,
      object_disappeared, object_count_exceeded, no_activity, density_high,
      class_ratio_exceeded, zone_inactive, forbidden_class_detected)
    - threshold: int for overcapacity/object_count_exceeded; seconds for dwell_exceeded
    - object_class: NULL = all observed classes in the ROI; otherwise filter
    - window_seconds: time window for evaluating the rule
    - enabled: soft-disable without delete
    """

    def list_by_roi(self, roi_id: str, enabled_only: bool = False) -> list[dict]:
        where = "WHERE roi_id = %s"
        params: list = [roi_id]
        if enabled_only:
            where += " AND enabled = TRUE"
        rows = execute_query(
            f"""
            SELECT id, roi_id, event_type, threshold, object_class,
                   window_seconds, enabled, created_at
            FROM roi_event_rule
            {where}
            ORDER BY event_type, object_class NULLS FIRST
            """,
            tuple(params),
            fetch="all",
        )
        return [
            {
                "id": str(row[0]), "roi_id": str(row[1]),
                "event_type": row[2], "threshold": row[3],
                "object_class": row[4], "window_seconds": row[5],
                "enabled": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
            }
            for row in rows
        ]

    def get_by_id(self, rule_id: str) -> dict | None:
        rows = execute_query(
            """
            SELECT id, roi_id, event_type, threshold, object_class,
                   window_seconds, enabled, created_at
            FROM roi_event_rule
            WHERE id = %s
            """,
            (rule_id,),
            fetch="all",
        )
        if not rows:
            return None
        row = rows[0]
        return {
            "id": str(row[0]), "roi_id": str(row[1]),
            "event_type": row[2], "threshold": row[3],
            "object_class": row[4], "window_seconds": row[5],
            "enabled": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        }

    def create(
        self,
        roi_id: str,
        event_type: str,
        threshold: int | None = None,
        object_class: str | None = None,
        window_seconds: int | None = None,
        enabled: bool = True,
    ) -> UUID:
        row = execute_query(
            """
            INSERT INTO roi_event_rule
                (roi_id, event_type, threshold, object_class, window_seconds, enabled)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (roi_id, event_type, threshold, object_class, window_seconds, enabled),
            fetch="one",
        )
        return row[0]

    def update(
        self,
        rule_id: str,
        *,
        event_type: str | None = None,
        threshold: int | None = None,
        object_class: str | None = None,
        window_seconds: int | None = None,
        enabled: bool | None = None,
    ) -> None:
        sets: list[str] = []
        params: list = []
        if event_type is not None:
            sets.append("event_type = %s"); params.append(event_type)
        if threshold is not None:
            sets.append("threshold = %s"); params.append(threshold)
        if object_class is not None:
            sets.append("object_class = %s"); params.append(object_class)
        if window_seconds is not None:
            sets.append("window_seconds = %s"); params.append(window_seconds)
        if enabled is not None:
            sets.append("enabled = %s"); params.append(enabled)
        if not sets:
            return
        params.append(rule_id)
        execute_query(
            f"UPDATE roi_event_rule SET {', '.join(sets)} WHERE id = %s",
            tuple(params), fetch=None,
        )

    def delete(self, rule_id: str) -> None:
        execute_query("DELETE FROM roi_event_rule WHERE id = %s", (rule_id,), fetch=None)
