# src/repositories/rule_repo.py
from uuid import UUID

from src.repositories.db import execute_query


class RuleRepository:
    def list_by_roi(self, roi_id: str) -> list[dict]:
        print(f"[DEBUG] RuleRepository.list_by_roi: ENTRY roi_id={roi_id}", flush=True)
        rows = execute_query(
            "SELECT id, roi_id, event_type, threshold, created_at FROM roi_event_rule WHERE roi_id = %s",
            (roi_id,),
            fetch="all",
        )
        return [
            {
                "id": str(row[0]), "roi_id": str(row[1]),
                "event_type": row[2], "threshold": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            }
            for row in rows
        ]

    def create(self, roi_id: str, event_type: str, threshold: int | None = None) -> UUID:
        print(f"[DEBUG] RuleRepository.create: ENTRY roi_id={roi_id} type={event_type}", flush=True)
        row = execute_query(
            "INSERT INTO roi_event_rule (roi_id, event_type, threshold) VALUES (%s, %s, %s) RETURNING id",
            (roi_id, event_type, threshold),
            fetch="one",
        )
        return row[0]

    def delete(self, rule_id: str) -> None:
        print(f"[DEBUG] RuleRepository.delete: ENTRY rule_id={rule_id}", flush=True)
        execute_query("DELETE FROM roi_event_rule WHERE id = %s", (rule_id,), fetch=None)
