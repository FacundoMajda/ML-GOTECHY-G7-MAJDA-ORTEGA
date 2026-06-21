# src/repositories/session_repo.py
import json
import uuid
from datetime import datetime
from uuid import UUID

from src.models.contracts import (
    OccupancySnapshot,
    SessionResult,
    TrackedEntityRecord,
    ZoneEventRecord,
)
from src.models.enums import TimestampMode
from src.repositories.db import execute_query


class SessionRepository:
    def create_session(self, session: SessionResult) -> UUID:
        session_uuid = uuid.uuid4()
        execute_query(
            """
            INSERT INTO detection_session (
                id, video_source_id, started_at, ended_at, timestamp_mode,
                fps, total_frames, write_video, output_video_path, extra_analysis
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(session_uuid),
                session.video_source_id,
                session.started_at,
                session.ended_at,
                session.timestamp_mode.value,
                session.fps,
                session.total_frames,
                session.write_video,
                session.output_video_path,
                json.dumps(session.extra_analysis) if session.extra_analysis else None,
            ),
        )
        return session_uuid

    def save_tracked_entities(
        self, session_id: UUID, entities: list[TrackedEntityRecord]
    ) -> None:
        for e in entities:
            execute_query(
                """
                INSERT INTO tracked_entity
                (id, session_id, track_id, first_seen_at, last_seen_at, first_seen_frame, last_seen_frame)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id, track_id) DO UPDATE
                SET last_seen_at = EXCLUDED.last_seen_at,
                    last_seen_frame = EXCLUDED.last_seen_frame
                """,
                (
                    str(uuid.uuid4()),
                    str(session_id),
                    e.track_id,
                    e.first_seen_at,
                    e.last_seen_at,
                    e.first_seen_frame,
                    e.last_seen_frame,
                ),
            )

    def save_occupancy_snapshot(
        self, session_id: UUID, snapshot: OccupancySnapshot
    ) -> None:
        execute_query(
            """
            INSERT INTO roi_occupancy_snapshot
            (session_id, roi_id, captured_at, frame_number, count_inside, count_outside, track_ids_inside)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(session_id),
                snapshot.roi_id,
                snapshot.captured_at,
                snapshot.frame_number,
                snapshot.count_inside,
                snapshot.count_outside,
                snapshot.track_ids_inside,
            ),
        )

    def save_zone_event(self, session_id: UUID, event: ZoneEventRecord) -> None:
        execute_query(
            """
            INSERT INTO zone_event
            (id, session_id, roi_id, track_id, event_type, occurred_at, frame_number, dwell_seconds, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                str(session_id),
                event.roi_id,
                event.track_id,
                event.event_type.value,
                event.occurred_at,
                event.frame_number,
                event.dwell_seconds,
                json.dumps(event.metadata),
            ),
        )

    def save_session_result(self, session: SessionResult) -> None:
        session_id = self.create_session(session)
        if session.tracked_entities:
            self.save_tracked_entities(session_id, session.tracked_entities)
        for snap in session.occupancy_snapshots:
            self.save_occupancy_snapshot(session_id, snap)
        for ev in session.zone_events:
            self.save_zone_event(session_id, ev)
