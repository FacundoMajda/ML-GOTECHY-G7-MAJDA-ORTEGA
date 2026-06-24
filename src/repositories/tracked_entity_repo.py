# src/repositories/tracked_entity_repo.py
import uuid
from uuid import UUID

from src.models.contracts import TrackedEntityRecord
from src.repositories.db import execute_batch


class TrackedEntityRepository:
    def save_all(self, session_id: UUID, entities: list[TrackedEntityRecord]) -> None:
        if not entities:
            print("[DEBUG] TrackedEntityRepository.save_all: 0 entities, skip", flush=True)
            return
        params_list = [
            (str(uuid.uuid4()), str(session_id), e.track_id, e.object_class,
             e.first_seen_at, e.last_seen_at, e.first_seen_frame, e.last_seen_frame)
            for e in entities
        ]
        print(f"[DEBUG] TrackedEntityRepository.save_all: batch insert n={len(params_list)}", flush=True)
        execute_batch(
            """
            INSERT INTO tracked_entity
            (id, session_id, track_id, object_class, first_seen_at, last_seen_at, first_seen_frame, last_seen_frame)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id, track_id) DO UPDATE
            SET last_seen_at = EXCLUDED.last_seen_at,
                last_seen_frame = EXCLUDED.last_seen_frame,
                object_class = EXCLUDED.object_class
            """,
            params_list,
        )
