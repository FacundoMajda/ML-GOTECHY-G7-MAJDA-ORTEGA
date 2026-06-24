# src/repositories/video_source_repo.py
from typing import Optional
from uuid import UUID

from src.models.contracts import VideoSourceConfig
from src.models.enums import SourceType
from src.repositories.db import execute_query


class VideoSourceRepository:
    def create(self, config: VideoSourceConfig) -> UUID:
        print(f"[DEBUG] VideoSourceRepository.create: ENTRY id={config.id} name={config.name}", flush=True)
        row = execute_query(
            """
            INSERT INTO video_source (id, name, source_type, source_uri, is_live)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (config.id, config.name, config.source_type.value, config.source_uri, config.is_live),
            fetch="one",
        )
        print(f"[DEBUG] VideoSourceRepository.create: returning {row[0]}", flush=True)
        return row[0]

    def get_by_id(self, video_id: str) -> Optional[VideoSourceConfig]:
        print(f"[DEBUG] VideoSourceRepository.get_by_id: ENTRY video_id={video_id}", flush=True)
        rows = execute_query(
            "SELECT id, name, source_type, source_uri, is_live FROM video_source WHERE id = %s",
            (video_id,),
            fetch="all",
        )
        if not rows:
            print(f"[DEBUG] VideoSourceRepository.get_by_id: not found, returning None", flush=True)
            return None
        row = rows[0]
        result = VideoSourceConfig(
            id=str(row[0]),
            name=row[1],
            source_type=SourceType(row[2]),
            source_uri=row[3],
            is_live=row[4],
        )
        print(f"[DEBUG] VideoSourceRepository.get_by_id: returning id={result.id} name={result.name}", flush=True)
        return result

    def list_all(self) -> list[VideoSourceConfig]:
        print(f"[DEBUG] VideoSourceRepository.list_all: ENTRY", flush=True)
        rows = execute_query(
            "SELECT id, name, source_type, source_uri, is_live FROM video_source ORDER BY created_at DESC",
            fetch="all",
        )
        result = [
            VideoSourceConfig(
                id=str(row[0]),
                name=row[1],
                source_type=SourceType(row[2]),
                source_uri=row[3],
                is_live=row[4],
            )
            for row in rows
        ]
        print(f"[DEBUG] VideoSourceRepository.list_all: returning {len(result)} sources", flush=True)
        return result

    def delete(self, video_id: str) -> None:
        print(f"[DEBUG] VideoSourceRepository.delete: ENTRY video_id={video_id}", flush=True)
        execute_query("DELETE FROM detection_session WHERE video_source_id = %s", (video_id,), fetch=None)
        execute_query("DELETE FROM video_source WHERE id = %s", (video_id,), fetch=None)
        print(f"[DEBUG] VideoSourceRepository.delete: done", flush=True)
