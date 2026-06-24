# src/repositories/alert_rule_repo.py
import uuid
from typing import Optional

from src.repositories.db import execute_query


class AlertRuleRepository:
    """Repository for alert_rule — composable rules per ROI.

    Schema reminder:
      - metric:   count | dwell_seconds | occupancy
      - operator: > | < | >= | <= | == | between
      - class_id: NULL = any observed class on the ROI
      - time_from / time_to: temporal window (NULL = always)
      - event_type: 'OccupancyHigh' | 'DwellExceeded' | 'ForbiddenClassDetected' | ...
      - severity:   info | warning | critical
    """

    def list_by_roi(self, roi_id: str) -> list[dict]:
        rows = execute_query(
            """
            SELECT id, roi_id, name, class_id, metric, operator,
                   threshold, threshold2, time_from, time_to,
                   event_type, severity, active, created_at
            FROM alert_rule
            WHERE roi_id = %s
            ORDER BY created_at DESC
            """,
            (roi_id,),
            fetch="all",
        )
        return [self._row_to_dict(r) for r in rows]

    def list_active(self, roi_id: Optional[str] = None) -> list[dict]:
        if roi_id is None:
            rows = execute_query(
                """
                SELECT id, roi_id, name, class_id, metric, operator,
                       threshold, threshold2, time_from, time_to,
                       event_type, severity, active, created_at
                FROM alert_rule
                WHERE active = TRUE
                """,
                fetch="all",
            )
        else:
            rows = execute_query(
                """
                SELECT id, roi_id, name, class_id, metric, operator,
                       threshold, threshold2, time_from, time_to,
                       event_type, severity, active, created_at
                FROM alert_rule
                WHERE roi_id = %s AND active = TRUE
                """,
                (roi_id,),
                fetch="all",
            )
        return [self._row_to_dict(r) for r in rows]

    def get_by_id(self, rule_id: str) -> dict | None:
        rows = execute_query(
            """
            SELECT id, roi_id, name, class_id, metric, operator,
                   threshold, threshold2, time_from, time_to,
                   event_type, severity, active, created_at
            FROM alert_rule
            WHERE id = %s
            """,
            (rule_id,),
            fetch="all",
        )
        return self._row_to_dict(rows[0]) if rows else None

    def create(
        self,
        roi_id: str,
        name: str,
        metric: str,
        operator: str,
        event_type: str,
        threshold: Optional[float] = None,
        threshold2: Optional[float] = None,
        class_id: Optional[int] = None,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
        severity: str = "warning",
        active: bool = True,
    ) -> uuid.UUID:
        rule_id = uuid.uuid4()
        row = execute_query(
            """
            INSERT INTO alert_rule
                (id, roi_id, name, class_id, metric, operator,
                 threshold, threshold2, time_from, time_to,
                 event_type, severity, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (str(rule_id), roi_id, name, class_id, metric, operator,
             threshold, threshold2, time_from, time_to,
             event_type, severity, active),
            fetch="one",
        )
        return row[0]

    def update(self, rule_id: str, **fields) -> None:
        allowed = {
            "name", "class_id", "metric", "operator", "threshold",
            "threshold2", "time_from", "time_to", "event_type",
            "severity", "active",
        }
        sets: list[str] = []
        params: list = []
        for key, val in fields.items():
            if key in allowed:
                sets.append(f"{key} = %s")
                params.append(val)
        if not sets:
            return
        params.append(rule_id)
        execute_query(
            f"UPDATE alert_rule SET {', '.join(sets)} WHERE id = %s",
            tuple(params), fetch=None,
        )

    def toggle_active(self, rule_id: str, active: bool) -> None:
        execute_query(
            "UPDATE alert_rule SET active = %s WHERE id = %s",
            (active, rule_id), fetch=None,
        )

    def delete(self, rule_id: str) -> None:
        execute_query("DELETE FROM alert_rule WHERE id = %s", (rule_id,), fetch=None)

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": str(row[0]),
            "roi_id": str(row[1]),
            "name": row[2],
            "class_id": row[3],
            "metric": row[4],
            "operator": row[5],
            "threshold": float(row[6]) if row[6] is not None else None,
            "threshold2": float(row[7]) if row[7] is not None else None,
            "time_from": str(row[8]) if row[8] is not None else None,
            "time_to": str(row[9]) if row[9] is not None else None,
            "event_type": row[10],
            "severity": row[11],
            "active": row[12],
            "created_at": row[13].isoformat() if row[13] else None,
        }
