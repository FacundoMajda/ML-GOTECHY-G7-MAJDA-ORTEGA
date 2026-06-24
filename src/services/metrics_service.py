import statistics
import uuid
from typing import Optional
from src.repositories.metric_snapshot_repo import MetricSnapshotRepository
from src.repositories.zone_event_repo import ZoneEventRepository
from src.repositories.occupancy_snapshot_repo import OccupancySnapshotRepository
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
        self.occupancy_repo = OccupancySnapshotRepository()

    def compute(self, session_id: uuid.UUID) -> list:
        """Compute MetricSnapshot for every (ROI, object_class) pair in a session.

        Reads all ZoneEvents for the session, aggregates per (roi, class),
        and persists one MetricSnapshot row per (session, roi, class) tuple.
        Multi-class: 1 ROI with 3 classes observadas → 3 rows.
        """
        zone_events = self.zone_event_repo.get_by_session(session_id)

        # Aggregate per (roi_id, object_class)
        agg: dict[tuple[uuid.UUID, str], dict] = {}
        for ze in zone_events:
            roi_id = ze["roi_id"]
            cls = ze.get("object_class") or "person"
            key = (roi_id, cls)
            if key not in agg:
                agg[key] = {
                    "entries": 0,
                    "exits": 0,
                    "occupancy": 0,
                    "peak_occupancy": 0,
                    "dwell_values": [],
                    "unique_tracks": set(),
                }

            m = agg[key]
            track_id = ze.get("track_id")
            if ze["event_type"] == "entry":
                m["entries"] += 1
                m["occupancy"] += 1
                if track_id is not None:
                    m["unique_tracks"].add(track_id)
            elif ze["event_type"] == "exit":
                m["exits"] += 1
                m["occupancy"] = max(0, m["occupancy"] - 1)
                if ze.get("dwell_seconds") is not None:
                    m["dwell_values"].append(float(ze["dwell_seconds"]))
                if track_id is not None:
                    m["unique_tracks"].add(track_id)

        # peak_occupancy real desde roi_occupancy_snapshot (no delta)
        for (roi_id, cls) in list(agg.keys()):
            peak = self.occupancy_repo.get_peak_occupancy(str(session_id), str(roi_id))
            agg[(roi_id, cls)]["peak_occupancy"] = peak

        # Persist one row per (roi, class)
        results = []
        for (roi_id, cls), m in agg.items():
            avg_dwell = (sum(m["dwell_values"]) / len(m["dwell_values"])) if m["dwell_values"] else None
            median_dwell = statistics.median(m["dwell_values"]) if m["dwell_values"] else None
            snap_id = self.snapshot_repo.save(
                session_id=session_id,
                roi_id=roi_id,
                object_class=cls,
                entries=m["entries"],
                exits=m["exits"],
                max_occupancy=m["peak_occupancy"],
                avg_dwell_seconds=avg_dwell,
                median_dwell_seconds=median_dwell,
                unique_objects=len(m["unique_tracks"]),
            )
            results.append({
                "id": snap_id, "roi_id": roi_id, "object_class": cls,
                "entries": m["entries"], "exits": m["exits"],
                "max_occupancy": m["peak_occupancy"],
                "unique_objects": len(m["unique_tracks"]),
                "avg_dwell_seconds": avg_dwell,
                "median_dwell_seconds": median_dwell,
            })

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

        # ── 12. Active alerts (rule-triggered events in last 24h) ──
        active_alerts = execute_query(
            """
            SELECT COUNT(*) FROM zone_event
            WHERE metadata IS NOT NULL
              AND metadata::jsonb ? 'rule_id'
              AND occurred_at >= NOW() - INTERVAL '24 hours'
            """, fetch="one",
        )
        active_alert_count = active_alerts[0] if active_alerts else 0

        # ── 13. Alerts by severity ──
        sev_raw = execute_query(
            """
            SELECT metadata->>'severity', COUNT(*)
            FROM zone_event
            WHERE metadata IS NOT NULL
              AND metadata::jsonb ? 'rule_id'
              AND occurred_at >= NOW() - INTERVAL '7 days'
            GROUP BY metadata->>'severity'
            """, fetch="all",
        )
        alerts_by_severity = {row[0]: row[1] for row in sev_raw} if sev_raw else {}

        # ── 14. Class distribution (top 10) ──
        cls_raw = execute_query(
            """
            SELECT object_class, COUNT(*) AS cnt
            FROM zone_event
            GROUP BY object_class
            ORDER BY cnt DESC
            LIMIT 10
            """, fetch="all",
        )
        class_distribution = [
            {"class": row[0], "count": row[1]} for row in cls_raw
        ] if cls_raw else []

        # ── 15. Alerts timeline (last 20 rule-triggered events) ──
        tl_raw = execute_query(
            """
            SELECT id::text, roi_id, event_type, occurred_at, object_class, metadata
            FROM zone_event
            WHERE metadata IS NOT NULL
              AND metadata::jsonb ? 'rule_id'
            ORDER BY occurred_at DESC
            LIMIT 20
            """, fetch="all",
        )
        alerts_timeline = []
        for row in tl_raw or []:
            md = row[5]
            if isinstance(md, str):
                import json
                try:
                    md = json.loads(md)
                except (json.JSONDecodeError, TypeError):
                    md = {}
            elif isinstance(md, dict) or md is None:
                pass
            else:
                md = {}
            alerts_timeline.append({
                "id": row[0],
                "roi_id": row[1],
                "event_type": row[2],
                "occurred_at": row[3].isoformat() if row[3] else None,
                "object_class": row[4],
                "severity": (md or {}).get("severity", "info"),
                "rule_name": (md or {}).get("rule_name", ""),
                "value": (md or {}).get("value"),
            })

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
            "active_alerts": active_alert_count,
            "alerts_by_severity": alerts_by_severity,
            "class_distribution": class_distribution,
            "alerts_timeline": alerts_timeline,
        }

    def get_roi_summary(self, roi_id: str) -> dict:
        """Mini-stats del ultimo session de un ROI: entries, exits, peak, dwell, tracks."""
        row = execute_query(
            """
            SELECT ds.id::text, ds.started_at, ds.ended_at,
                   COALESCE(SUM(ms.entries), 0)  AS entries,
                   COALESCE(SUM(ms.exits), 0)    AS exits,
                   COALESCE(AVG(ms.avg_dwell_seconds), 0) AS avg_dwell_seconds,
                   COALESCE(SUM(ms.unique_objects), 0) AS unique_tracks
            FROM roi r
            LEFT JOIN detection_session ds ON ds.video_source_id = r.video_source_id AND ds.status = 'completed'
            LEFT JOIN metric_snapshot ms ON ms.session_id = ds.id AND ms.roi_id = r.id
            WHERE r.id = %s
            GROUP BY ds.id, ds.started_at, ds.ended_at
            ORDER BY ds.started_at DESC NULLS LAST
            LIMIT 1
            """,
            (roi_id,),
            fetch="one",
        )
        if not row:
            return {"has_data": False, "session_id": None}
        session_id = row[0]
        # peak_occupancy real desde snapshots de occupancy (no delta de events)
        peak_occupancy = self.occupancy_repo.get_peak_occupancy(session_id, roi_id)
        return {
            "has_data": True,
            "session_id": session_id,
            "started_at": row[1].isoformat() if row[1] else None,
            "duration_seconds": (row[2] - row[1]).total_seconds() if (row[1] and row[2]) else None,
            "entries": int(row[3]),
            "exits": int(row[4]),
            "peak_occupancy": peak_occupancy,
            "avg_dwell_seconds": round(float(row[5]), 1) if row[5] else 0,
            "unique_tracks": int(row[6]),
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

    def get_timeline(self, hours: int = 24) -> dict:
        """Time series agrupado por hora y clase para visualizacion."""
        rows = execute_query(
            """
            SELECT
                date_trunc('hour', occurred_at) AS bucket,
                COALESCE(NULLIF(object_class, ''), 'any') AS cls,
                COUNT(*) AS cnt
            FROM zone_event
            WHERE event_type IN ('entry', 'exit')
              AND occurred_at >= NOW() - make_interval(hours => %s)
            GROUP BY 1, 2
            ORDER BY 1
            """,
            (hours,),
            fetch="all",
        )
        # Pivot: { "2026-06-23T18:00:00": { "person": 12, "car": 4 }, ... }
        timeline: dict[str, dict[str, int]] = {}
        classes: set[str] = set()
        for bucket, cls, cnt in rows or []:
            key = bucket.isoformat() if bucket else "unknown"
            timeline.setdefault(key, {})[cls] = cnt
            classes.add(cls)
        return {
            "hours": hours,
            "classes": sorted(classes),
            "timeline": timeline,
        }

    def get_session_tracks(self, session_id: str) -> list:
        """Tracks de un session con entries/exits/dwell por track."""
        rows = execute_query(
            """
            SELECT te.track_id::text,
                   te.object_class,
                   te.first_seen_at,
                   te.last_seen_at,
                   COUNT(*) FILTER (WHERE ze.event_type = 'entry') AS entries,
                   COUNT(*) FILTER (WHERE ze.event_type = 'exit')  AS exits,
                   COALESCE(MAX(ze.dwell_seconds), 0)             AS max_dwell
            FROM tracked_entity te
            LEFT JOIN zone_event ze ON ze.track_id = te.track_id AND ze.session_id = %s
            WHERE te.session_id = %s
            GROUP BY te.track_id, te.object_class, te.first_seen_at, te.last_seen_at
            ORDER BY max_dwell DESC NULLS LAST
            LIMIT 50
            """,
            (session_id, session_id),
            fetch="all",
        )
        return [{
            "track_id": r[0],
            "object_class": r[1] or "person",
            "first_seen_at": r[2].isoformat() if r[2] else None,
            "last_seen_at": r[3].isoformat() if r[3] else None,
            "entries": int(r[4] or 0),
            "exits": int(r[5] or 0),
            "max_dwell_seconds": float(r[6] or 0),
        } for r in rows or []]

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
