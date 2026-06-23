# src/repositories/tracked_entity_repo.py
import uuid
from uuid import UUID

from src.models.contracts import TrackedEntityRecord
from src.repositories.db import execute_query


class TrackedEntityRepository:
    def save_all(self, session_id: UUID, entities: list[TrackedEntityRecord]) -> None:
        print(f"[DEBUG] TrackedEntityRepository.save_all: ENTRY session_id={session_id} n_entities={len(entities)}", flush=True)
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
                (str(uuid.uuid4()), str(session_id), e.track_id,
                 e.first_seen_at, e.last_seen_at, e.first_seen_frame, e.last_seen_frame),
                fetch=None,
            )
