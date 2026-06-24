# src/services/rule_evaluator.py
from datetime import datetime, time
from typing import Optional

from src.models.contracts import ZoneEventRecord
from src.models.enums import EventType


# Lazy cache: class_id (int) -> class name (str).
# Populated on first evaluate() call from catalog repo.
_CLASS_BY_ID: dict[int, str] = {}


def _resolve_class_name(class_id: Optional[int]) -> str:
    if class_id is None:
        return "any"
    if class_id in _CLASS_BY_ID:
        return _CLASS_BY_ID[class_id]
    return f"class_{class_id}"


def _hydrate_class_cache() -> None:
    if _CLASS_BY_ID:
        return
    try:
        from src.repositories.class_catalog_repo import ObjectClassCatalogRepository
        for cls in ObjectClassCatalogRepository().list_all():
            _CLASS_BY_ID[cls["id"]] = cls["name"]
    except Exception:
        pass


class RuleEvaluator:
    """Evaluates alert_rule rows against each periodic ROI snapshot.

    Called from CounterEngine every SNAPSHOT_INTERVAL frames.
    Cache of active rules per ROI is built once at start of analysis
    (cheaper than re-querying per frame).
    """

    def __init__(self, roi_id: str, rules: list[dict]):
        self.roi_id = roi_id
        self.rules = rules
        _hydrate_class_cache()

    def evaluate(
        self,
        timestamp: datetime,
        frame_index: int,
        class_counts: dict,
        current_occupancy: int,
        last_dwell_seconds: Optional[float] = None,
    ) -> list[ZoneEventRecord]:
        new_events: list[ZoneEventRecord] = []
        for rule in self.rules:
            if not rule.get("active", True):
                continue
            if not self._in_time_window(rule, timestamp):
                continue
            value = self._metric_value(
                rule, class_counts, current_occupancy, last_dwell_seconds
            )
            if value is None:
                continue
            if not self._check_condition(value, rule):
                continue
            cls_name = _resolve_class_name(rule.get("class_id"))
            new_events.append(
                ZoneEventRecord(
                    roi_id=self.roi_id,
                    event_type=EventType.OVERCAPACITY,  # bucket — the event_type from rule goes in metadata
                    occurred_at=timestamp,
                    frame_number=frame_index,
                    object_class=cls_name,
                    metadata={
                        "rule_id": str(rule["id"]),
                        "rule_name": rule["name"],
                        "event_type": rule["event_type"],
                        "severity": rule["severity"],
                        "value": value,
                        "threshold": rule.get("threshold"),
                        "operator": rule["operator"],
                    },
                )
            )
        return new_events

    @staticmethod
    def _metric_value(
        rule: dict,
        class_counts: dict,
        current_occupancy: int,
        last_dwell_seconds: Optional[float],
    ) -> Optional[float]:
        metric = rule.get("metric")
        class_id = rule.get("class_id")
        if metric == "count":
            if class_id is None:
                return float(sum(class_counts.values()))
            cls_name = _resolve_class_name(class_id)
            return float(class_counts.get(cls_name, 0))
        if metric == "occupancy":
            return float(current_occupancy)
        if metric == "dwell_seconds":
            return last_dwell_seconds
        return None

    @staticmethod
    def _check_condition(value: float, rule: dict) -> bool:
        op = rule["operator"]
        t1 = rule.get("threshold")
        t2 = rule.get("threshold2")
        if t1 is None:
            return False
        try:
            if op == ">": return value > t1
            if op == "<": return value < t1
            if op == ">=": return value >= t1
            if op == "<=": return value <= t1
            if op == "==": return value == t1
            if op == "between": return t1 <= value <= (t2 if t2 is not None else t1)
        except TypeError:
            return False
        return False

    @staticmethod
    def _in_time_window(rule: dict, now: datetime) -> bool:
        t_from = rule.get("time_from")
        t_to = rule.get("time_to")
        if not t_from and not t_to:
            return True
        cur = now.time()
        if t_from:
            try:
                if cur < _parse_time(t_from):
                    return False
            except (TypeError, ValueError):
                pass
        if t_to:
            try:
                if cur > _parse_time(t_to):
                    return False
            except (TypeError, ValueError):
                pass
        return True


def _parse_time(s: str) -> time:
    """Parse HH:MM or HH:MM:SS string to datetime.time."""
    parts = s.split(":")
    return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
