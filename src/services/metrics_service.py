import uuid
from typing import Optional
from src.repositories.metric_snapshot_repo import MetricSnapshotRepository
from src.repositories.zone_event_repo import ZoneEventRepository
from src.repositories.db import get_db_pool


class MetricsService:
    """Computes and retrieves derived metrics from ZoneEvents.

    MetricsService is PURE derivation — no tracking, no detection logic.
    All metrics are recomputable from ZoneEvents at any time.

    Boundaries:
        OK: aggregations, projections, dashboards, trends, comparisons
        NOT OK: tracking logic, event logic, detection logic
    """

    def __init__(self):
        self.snapshot_repo = MetricSnapshotRepository()
        self.zone_event_repo = ZoneEventRepository()

    def compute(self, session_id: uuid.UUID) -> list:
        """Compute MetricSnapshot for every ROI in a session.

        Reads all ZoneEvents for the session, aggregates per ROI,
        and persists the result as MetricSnapshot rows.
        """
        zone_events = self.zone_event_repo.get_by_session(session_id)

        # Aggregate per roi_id
        roi_metrics: dict[uuid.UUID, dict] = {}
        for ze in zone_events:
            roi_id = ze["roi_id"]
            if roi_id not in roi_metrics:
                roi_metrics[roi_id] = {
                    "entries": 0,
                    "exits": 0,
                    "occupancy": 0,
                    "peak_occupancy": 0,
                    "dwell_sum": 0.0,
                    "dwell_count": 0,
                }

            m = roi_metrics[roi_id]
            if ze["event_type"] == "entry":
                m["entries"] += 1
                m["occupancy"] += 1
                m["peak_occupancy"] = max(m["peak_occupancy"], m["occupancy"])
            elif ze["event_type"] == "exit":
                m["exits"] += 1
                m["occupancy"] = max(0, m["occupancy"] - 1)
            elif ze["event_type"] == "dwell" and ze.get("dwell_seconds"):
                m["dwell_sum"] += ze["dwell_seconds"]
                m["dwell_count"] += 1

        # Persist
        results = []
        for roi_id, m in roi_metrics.items():
            avg_dwell = (m["dwell_sum"] / m["dwell_count"]) if m["dwell_count"] > 0 else None
            snap_id = self.snapshot_repo.save(
                session_id=session_id,
                roi_id=roi_id,
                entries=m["entries"],
                exits=m["exits"],
                max_occupancy=m["peak_occupancy"],
                avg_dwell_seconds=avg_dwell,
            )
            results.append({"id": snap_id, "roi_id": roi_id, **m})

        return results

    def get_dashboard(self) -> dict:
        """Aggregate totals across all sessions."""
        pool = get_db_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(entries), 0)   AS total_entries,
                        COALESCE(SUM(exits), 0)     AS total_exits,
                        COALESCE(SUM(max_occupancy), 0) AS sum_peak,
                        COUNT(DISTINCT session_id)  AS session_count
                    FROM metric_snapshot
                    """
                )
                row = cur.fetchone()
                return {
                    "total_entries": row[0] or 0,
                    "total_exits": row[1] or 0,
                    "sum_peak": row[2] or 0,
                    "session_count": row[3] or 0,
                }

    def get_trend(self, roi_id: uuid.UUID) -> list:
        """Time series of entries/exits per session for a ROI."""
        pool = get_db_pool()
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ms.session_id, ms.entries, ms.exits, ms.max_occupancy,
                           ds.started_at
                    FROM metric_snapshot ms
                    JOIN detection_session ds ON ds.id = ms.session_id
                    WHERE ms.roi_id = %s
                    ORDER BY ds.started_at
                    """,
                    (str(roi_id),),
                )
                rows = cur.fetchall()
                return [
                    {
                        "session_id": r[0],
                        "entries": r[1],
                        "exits": r[2],
                        "max_occupancy": r[3],
                        "started_at": r[4],
                    }
                    for r in rows
                ]

    def compare(self, session_a: uuid.UUID, session_b: uuid.UUID) -> dict:
        """Compare metrics between two sessions."""
        a_snaps = self.snapshot_repo.get_by_session(session_a)
        b_snaps = self.snapshot_repo.get_by_session(session_b)

        def sum_metrics(snaps):
            return {
                "entries": sum(s["entries"] for s in snaps),
                "exits": sum(s["exits"] for s in snaps),
                "max_occupancy": max((s["max_occupancy"] for s in snaps), default=0),
            }

        ma = sum_metrics(a_snaps)
        mb = sum_metrics(b_snaps)

        return {
            "session_a": {"session_id": session_a, **ma},
            "session_b": {"session_id": session_b, **mb},
            "diff_entries": ma["entries"] - mb["entries"],
            "diff_exits": ma["exits"] - mb["exits"],
        }
