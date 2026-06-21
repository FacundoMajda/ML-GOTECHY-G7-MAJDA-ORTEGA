# src/services/analytics_service.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO

from src.config.settings import OUTPUT_DIR, REPORTS_DIR, YOLO_MODEL_PATH
from src.models.contracts import (
    OccupancySnapshot,
    ROIConfig,
    SessionResult,
    TimestampMode,
    TrackedEntityRecord,
    VideoSourceConfig,
    ZoneEventRecord,
)
from src.models.enums import EventType
from src.providers.base import FrameProvider
from src.providers.factory import VideoSourceFactory
from src.repositories.session_repo import SessionRepository


@dataclass
class EntityState:
    track_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    first_seen_frame: int
    last_seen_frame: int
    inside_rois: dict[str, bool]  # roi_id -> inside


class CounterEngine:
    SNAPSHOT_INTERVAL = 30  # frames entre snapshots de occupancia

    def __init__(self, roi_configs: list[ROIConfig]):
        self.roi_configs = {r.id: r for r in roi_configs}
        self.roi_polygons = {
            r.id: np.array(r.polygon, dtype=np.int32) for r in roi_configs
        }
        self.zone_state: dict[str, dict[int, bool]] = {
            r.id: {} for r in roi_configs
        }
        self.zone_counts: dict[str, dict[str, int]] = {
            r.id: {"entry": 0, "exit": 0} for r in roi_configs
        }
        self.entity_states: dict[int, EntityState] = {}
        self.events: list[ZoneEventRecord] = []
        self.snapshots: list[OccupancySnapshot] = []
        self._frame_index = 0

    def is_inside(self, roi_id: str, point: tuple[float, float]) -> bool:
        return cv2.pointPolygonTest(
            self.roi_polygons[roi_id], point, measureDist=False
        ) >= 0

    def update(
        self,
        frame_index: int,
        track_id: int,
        center: tuple[float, float],
        foot: tuple[float, float],
        timestamp: datetime,
    ) -> None:
        self._frame_index = frame_index
        now = timestamp

        # Init or update entity state
        if track_id not in self.entity_states:
            self.entity_states[track_id] = EntityState(
                track_id=track_id,
                first_seen_at=now,
                last_seen_at=now,
                first_seen_frame=frame_index,
                last_seen_frame=frame_index,
                inside_rois={},
            )
        else:
            state = self.entity_states[track_id]
            state.last_seen_at = now
            state.last_seen_frame = frame_index

        # Check each ROI
        for roi_id, roi in self.roi_configs.items():
            inside = self.is_inside(roi_id, foot)
            prev = self.zone_state[roi_id].get(track_id)

            if prev is False and inside:
                self.zone_counts[roi_id]["entry"] += 1
                self.events.append(
                    ZoneEventRecord(
                        roi_id=roi_id,
                        event_type=EventType.ENTRY,
                        occurred_at=now,
                        track_id=track_id,
                        frame_number=frame_index,
                    )
                )
            elif prev is True and not inside:
                self.zone_counts[roi_id]["exit"] += 1
                dwell = (now - self.entity_states[track_id].first_seen_at).total_seconds()
                self.events.append(
                    ZoneEventRecord(
                        roi_id=roi_id,
                        event_type=EventType.EXIT,
                        occurred_at=now,
                        track_id=track_id,
                        frame_number=frame_index,
                        dwell_seconds=dwell,
                    )
                )

            self.zone_state[roi_id][track_id] = inside
            self.entity_states[track_id].inside_rois[roi_id] = inside

        # Periodic snapshot
        if frame_index % self.SNAPSHOT_INTERVAL == 0:
            self._take_snapshot(timestamp)

    def _take_snapshot(self, timestamp: datetime) -> None:
        total_tracked = len(self.entity_states)
        for roi_id in self.roi_configs:
            inside_ids = [
                tid for tid, inside in self.zone_state[roi_id].items() if inside
            ]
            self.snapshots.append(
                OccupancySnapshot(
                    roi_id=roi_id,
                    captured_at=timestamp,
                    frame_number=self._frame_index,
                    count_inside=len(inside_ids),
                    count_outside=total_tracked - len(inside_ids),
                    track_ids_inside=inside_ids,
                )
            )

    def get_tracked_entities(self) -> list[TrackedEntityRecord]:
        return [
            TrackedEntityRecord(
                track_id=state.track_id,
                first_seen_at=state.first_seen_at,
                last_seen_at=state.last_seen_at,
                first_seen_frame=state.first_seen_frame,
                last_seen_frame=state.last_seen_frame,
            )
            for state in self.entity_states.values()
        ]


# ── Model cache (singleton lazy) ────────────────────────────────────────────
_model_instance: YOLO | None = None


def _get_model() -> YOLO:
    global _model_instance
    if _model_instance is None:
        path = Path(YOLO_MODEL_PATH)
        if not path.exists():
            raise FileNotFoundError(
                f"Modelo YOLO no encontrado en {YOLO_MODEL_PATH}. "
                f"Asegurate de tener el .pt en src/inference/"
            )
        _model_instance = YOLO(path)
    return _model_instance


class AnalyticsService:
    def __init__(
        self,
        config: VideoSourceConfig,
        roi_configs: list[ROIConfig],
        persist: bool = False,
    ):
        self.config = config
        self.roi_configs = roi_configs
        self.provider: FrameProvider = VideoSourceFactory.create(config)
        self.persist = persist
        self._session_repo = SessionRepository() if persist else None

    def process(
        self,
        write_video: bool = True,
        extra_analysis: Optional[dict] = None,
    ) -> SessionResult:
        model = _get_model()
        engine = CounterEngine(self.roi_configs)

        out_path = None
        writer = None

        OUTPUT_PATH = Path(OUTPUT_DIR)
        OUTPUT_PATH.mkdir(exist_ok=True)
        REPORTS_PATH = Path(REPORTS_DIR)
        REPORTS_PATH.mkdir(exist_ok=True)

        started_at = datetime.now()
        frame_index = 0
        timestamp_mode = TimestampMode.REALTIME if self.provider.is_live else TimestampMode.FRAME_BASED

        while True:
            frame = self.provider.next_frame()
            if frame is None:
                break

            if write_video and writer is None:
                h, w = frame.shape[:2]
                fps = self.provider.get_fps() or 30.0
                out_path = OUTPUT_PATH / f"{self.config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                writer = cv2.VideoWriter(
                    str(out_path),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (w, h),
                )

            results = model.track(
                frame,
                persist=True,
                verbose=False,
                classes=[0],
                conf=0.3,
                tracker="bytetrack.yaml",
            )

            result = results[0]
            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                ids = result.boxes.id.cpu().numpy().astype(int)

                for bbox, track_id in zip(boxes, ids):
                    x1, y1, x2, y2 = bbox
                    foot = ((x1 + x2) / 2.0, y2)
                    center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                    ts = datetime.now() if timestamp_mode == TimestampMode.REALTIME else started_at
                    engine.update(frame_index, int(track_id), center, foot, ts)

            if writer:
                writer.write(frame)

            frame_index += 1

        if writer:
            writer.release()

        ended_at = datetime.now()
        # Final snapshot
        engine._take_snapshot(ended_at)

        session_result = SessionResult(
            video_source_id=self.config.id,
            timestamp_mode=timestamp_mode,
            started_at=started_at,
            ended_at=ended_at,
            fps=self.provider.get_fps(),
            total_frames=frame_index,
            write_video=write_video,
            output_video_path=str(out_path) if out_path else None,
            extra_analysis=extra_analysis,
            tracked_entities=engine.get_tracked_entities(),
            occupancy_snapshots=engine.snapshots,
            zone_events=engine.events,
        )

        if self.persist and self._session_repo:
            self._session_repo.save_session_result(session_result)

        return session_result
