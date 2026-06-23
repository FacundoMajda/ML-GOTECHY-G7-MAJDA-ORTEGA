import uuid
from typing import Optional
from src.repositories.metric_snapshot_repo import MetricSnapshotRepository
from src.repositories.zone_event_repo import ZoneEventRepository
from src.repositories.db import execute_query


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
        """Aggregate real metrics across all entities for the dashboard."""
        # ── 1. Summary counts ──
        summary = execute_query(
            """
            SELECT
                COALESCE(SUM(entries), 0),
                COALESCE(SUM(exits), 0),
                COUNT(DISTINCT session_id),
                COALESCE(SUM(max_occupancy), 0)
            FROM metric_snapshot
            """, fetch="one",
        )
        total_entries = summary[0] if summary else 0
        total_exits   = summary[1] if summary else 0
        session_count = summary[2] if summary else 0

        # ── 2. Unique entities tracked ──
        ent = execute_query(
            "SELECT COUNT(DISTINCT track_id) FROM tracked_entity", fetch="one",
        )
        total_entities = ent[0] if ent else 0

        # ── 3. Sources & ROIs ──
        src = execute_query(
            """
            SELECT
                (SELECT COUNT(*) FROM video_source),
                (SELECT COUNT(DISTINCT video_source_id) FROM roi)
            """, fetch="one",
        )
        total_sources     = src[0] if src else 0
        sources_with_rois = src[1] if src else 0

        # ── 4. Total hours analyzed ──
        hrs = execute_query(
            """
            SELECT COALESCE(EXTRACT(EPOCH FROM SUM(ended_at - started_at)), 0) / 3600.0
            FROM detection_session WHERE ended_at IS NOT NULL AND status = 'completed'
            """, fetch="one",
        )
        total_hours = round(float(hrs[0]), 1) if hrs and hrs[0] else 0

        # ── 5. Average occupancy across all snapshots ──
        occ = execute_query(
            "SELECT COALESCE(AVG(count_inside), 0) FROM roi_occupancy_snapshot",
            fetch="one",
        )
        avg_occupancy = round(float(occ[0]), 1) if occ else 0

        # ── 6. Average dwell time ──
        dwl = execute_query(
            """
            SELECT COALESCE(AVG(avg_dwell_seconds), 0)
            FROM metric_snapshot WHERE avg_dwell_seconds IS NOT NULL
            """, fetch="one",
        )
        avg_dwell = round(float(dwl[0]), 1) if dwl else 0

        # ── 7. Analysis success rate ──
        st = execute_query(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'completed'),
                COUNT(*) FILTER (WHERE status = 'failed')
            FROM detection_session
            """, fetch="one",
        )
        completed = st[0] if st else 0
        failed    = st[1] if st else 0
        total_analyses = completed + failed

        # ── 8. Top 5 ROIs by activity ──
        rois_raw = execute_query(
            """
            SELECT r.name, SUM(ms.entries), SUM(ms.exits)
            FROM metric_snapshot ms
            JOIN roi r ON r.id = ms.roi_id
            GROUP BY r.id, r.name
            ORDER BY SUM(ms.entries) + SUM(ms.exits) DESC
            LIMIT 5
            """, fetch="all",
        )
        top_rois = [
            {"name": row[0], "entries": row[1] or 0, "exits": row[2] or 0}
            for row in rois_raw
        ]

        # ── 9. Events grouped by video source ──
        evsrc_raw = execute_query(
            """
            SELECT vs.name, SUM(ms.entries), SUM(ms.exits)
            FROM metric_snapshot ms
            JOIN detection_session ds ON ds.id = ms.session_id
            JOIN video_source vs ON vs.id = ds.video_source_id
            GROUP BY vs.id, vs.name
            ORDER BY SUM(ms.entries) + SUM(ms.exits) DESC
            LIMIT 5
            """, fetch="all",
        )
        events_by_source = [
            {"source_name": row[0], "entries": row[1] or 0, "exits": row[2] or 0}
            for row in evsrc_raw
        ]

        # ── 10. Last 5 analyses ──
        recent_raw = execute_query(
            """
            SELECT ds.id::text, vs.name, ds.started_at,
                COALESCE(EXTRACT(EPOCH FROM (ds.ended_at - ds.started_at)), 0)::float,
                ds.status
            FROM detection_session ds
            JOIN video_source vs ON vs.id = ds.video_source_id
            ORDER BY ds.started_at DESC NULLS LAST
            LIMIT 5
            """, fetch="all",
        )
        recent_sessions = [
            {
                "id": row[0],
                "source_name": row[1],
                "started_at": row[2].isoformat() if row[2] else None,
                "duration_seconds": row[3] or 0,
                "status": row[4] or "completed",
            }
            for row in recent_raw
        ]

        # ── 11. Hourly event distribution (last 7 days) ──
        hourly_raw = execute_query(
            """
            SELECT
                EXTRACT(HOUR FROM occurred_at)::int,
                COUNT(*) FILTER (WHERE event_type = 'entry'),
                COUNT(*) FILTER (WHERE event_type = 'exit')
            FROM zone_event
            WHERE occurred_at >= NOW() - INTERVAL '7 days'
            GROUP BY 1
            ORDER BY 1
            """, fetch="all",
        )
        hourly_distribution = [
            {"hour": row[0], "entries": row[1] or 0, "exits": row[2] or 0}
            for row in hourly_raw
        ]

        return {
            "total_entries": total_entries,
            "total_exits": total_exits,
            "session_count": session_count,
            "total_entities": total_entities,
            "total_sources": total_sources,
            "sources_with_rois": sources_with_rois,
            "total_hours_analyzed": total_hours,
            "avg_occupancy": avg_occupancy,
            "avg_dwell_seconds": avg_dwell,
            "completed_analyses": completed,
            "failed_analyses": failed,
            "total_analyses": total_analyses,
            "top_rois": top_rois,
            "events_by_source": events_by_source,
            "recent_sessions": recent_sessions,
            "hourly_distribution": hourly_distribution,
        }

    def get_trend(self, roi_id: uuid.UUID) -> list:
        """Time series of entries/exits per session for a ROI."""
        rows = execute_query(
            """
            SELECT ms.session_id, ms.entries, ms.exits, ms.max_occupancy,
                   ds.started_at
            FROM metric_snapshot ms
            JOIN detection_session ds ON ds.id = ms.session_id
            WHERE ms.roi_id = %s
            ORDER BY ds.started_at
            """,
            (str(roi_id),),
            fetch="all",
        )
        if not rows:
            return []
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
