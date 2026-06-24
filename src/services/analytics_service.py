# src/services/analytics_service.py
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

import cv2
import numpy as np

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
from src.repositories.occupancy_snapshot_repo import OccupancySnapshotRepository
from src.repositories.session_repo import SessionRepository
from src.repositories.tracked_entity_repo import TrackedEntityRepository
from src.repositories.zone_event_repo import ZoneEventRepository
from src.services.metrics_service import MetricsService


# ── YOLO COCO class id → nombre semántico ────────────────────
# Mapeo extendido del catálogo COCO que el modelo YOLO11n detecta.
# Si un id no está acá, fallback a "class_<n>".
_YOLO_ID_TO_CLASS: dict[int, str] = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    15: "cat",
    16: "dog",
    24: "backpack",
    26: "suitcase",
    27: "umbrella",
    28: "handbag",
    39: "bottle",
    41: "cup",
    56: "chair",
    57: "couch",
    58: "potted_plant",
    60: "dining_table",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell_phone",
    73: "book",
}


@dataclass
class EntityState:
    track_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    first_seen_frame: int
    last_seen_frame: int
    object_class: str = "person"
    inside_rois: dict[str, bool] = field(default_factory=dict)  # roi_id -> inside
    roi_entry_started_at: dict[str, datetime] = field(default_factory=dict)


class CounterEngine:
    SNAPSHOT_INTERVAL = 30  # frames entre snapshots de occupancia

    def __init__(self, roi_configs: list[ROIConfig], alert_rules_by_roi: dict | None = None):
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
        self.zone_unique_tracks: dict[str, dict[str, set[int]]] = {
            r.id: {"entry": set(), "exit": set()} for r in roi_configs
        }
        self.entity_states: dict[int, EntityState] = {}
        self.events: list[ZoneEventRecord] = []
        self.snapshots: list[OccupancySnapshot] = []
        self._frame_index = 0
        # Rule engine: per-ROI active alert rules (read from alert_rule table)
        self._alert_rules_by_roi: dict[str, list[dict]] = alert_rules_by_roi or {}

    @staticmethod
    def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    @staticmethod
    def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
        return (
            min(a[0], b[0]) <= c[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])
        )

    @classmethod
    def _segments_intersect(
        cls,
        p1: tuple[float, float],
        p2: tuple[float, float],
        q1: tuple[float, float],
        q2: tuple[float, float],
    ) -> bool:
        eps = 1e-6
        o1 = cls._orientation(p1, p2, q1)
        o2 = cls._orientation(p1, p2, q2)
        o3 = cls._orientation(q1, q2, p1)
        o4 = cls._orientation(q1, q2, p2)

        if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
            return True
        if abs(o1) < eps and cls._on_segment(p1, p2, q1):
            return True
        if abs(o2) < eps and cls._on_segment(p1, p2, q2):
            return True
        if abs(o3) < eps and cls._on_segment(q1, q2, p1):
            return True
        if abs(o4) < eps and cls._on_segment(q1, q2, p2):
            return True
        return False

    def is_inside(self, roi_id: str, foot_left: tuple[float, float], foot_right: tuple[float, float]) -> bool:
        polygon = self.roi_polygons[roi_id]
        foot_center = ((foot_left[0] + foot_right[0]) / 2.0, (foot_left[1] + foot_right[1]) / 2.0)

        if cv2.pointPolygonTest(polygon, foot_center, measureDist=False) >= 0:
            return True

        pts = [tuple(map(float, pt)) for pt in polygon.tolist()]
        for idx in range(len(pts)):
            seg_start = pts[idx]
            seg_end = pts[(idx + 1) % len(pts)]
            if self._segments_intersect(foot_left, foot_right, seg_start, seg_end):
                return True
        return False

    def update(
        self,
        frame_index: int,
        track_id: int,
        center: tuple[float, float],
        foot_left: tuple[float, float],
        foot_right: tuple[float, float],
        timestamp: datetime,
        object_class: str = "person",
    ) -> None:
        print(f"[DEBUG] CounterEngine.update: ENTRY frame_index={frame_index} track_id={track_id} class={object_class} foot_left=({foot_left[0]:.1f},{foot_left[1]:.1f}) foot_right=({foot_right[0]:.1f},{foot_right[1]:.1f})", flush=True)
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
                object_class=object_class,
            )
            print(f"[DEBUG] CounterEngine.update: new entity_state for track_id={track_id} class={object_class}", flush=True)
        else:
            state = self.entity_states[track_id]
            state.last_seen_at = now
            state.last_seen_frame = frame_index

        # Check each ROI
        for roi_id, roi in self.roi_configs.items():
            # KISS: only count this class in this ROI if it's observed
            # (object_class comes from YOLO; ROI.observed_classes is the filter)
            if object_class not in roi.observed_classes:
                # still update state so it doesn't get "stuck" if class changes
                self.zone_state[roi_id][track_id] = False
                self.entity_states[track_id].inside_rois[roi_id] = False
                continue
            inside = self.is_inside(roi_id, foot_left, foot_right)
            prev = self.zone_state[roi_id].get(track_id)

            if prev in (None, False) and inside and roi.detect_entry:
                self.zone_counts[roi_id]["entry"] += 1
                self.zone_unique_tracks[roi_id]["entry"].add(track_id)
                self.entity_states[track_id].roi_entry_started_at[roi_id] = now
                self.events.append(
                    ZoneEventRecord(
                        roi_id=roi_id,
                        event_type=EventType.ENTRY,
                        occurred_at=now,
                        track_id=track_id,
                        frame_number=frame_index,
                        object_class=object_class,
                    )
                )
                print(f"[DEBUG] CounterEngine.update: ENTRY event roi={roi_id} track={track_id} class={object_class}", flush=True)
            elif prev is True and not inside and roi.detect_exit:
                self.zone_counts[roi_id]["exit"] += 1
                self.zone_unique_tracks[roi_id]["exit"].add(track_id)
                entry_started_at = self.entity_states[track_id].roi_entry_started_at.get(
                    roi_id, self.entity_states[track_id].first_seen_at
                )
                dwell = (now - entry_started_at).total_seconds()
                self.events.append(
                    ZoneEventRecord(
                        roi_id=roi_id,
                        event_type=EventType.EXIT,
                        occurred_at=now,
                        track_id=track_id,
                        frame_number=frame_index,
                        dwell_seconds=dwell,
                        object_class=object_class,
                    )
                )
                print(f"[DEBUG] CounterEngine.update: EXIT event roi={roi_id} track={track_id} dwell={dwell:.1f}s class={object_class}", flush=True)
                self.entity_states[track_id].roi_entry_started_at.pop(roi_id, None)

            self.zone_state[roi_id][track_id] = inside
            self.entity_states[track_id].inside_rois[roi_id] = inside

        # Periodic snapshot
        if frame_index % self.SNAPSHOT_INTERVAL == 0:
            self._take_snapshot(timestamp)

    def _take_snapshot(self, timestamp: datetime) -> None:
        print(f"[DEBUG] CounterEngine._take_snapshot: ENTRY frame={self._frame_index} ents={len(self.entity_states)}", flush=True)
        total_tracked = len(self.entity_states)
        for roi_id in self.roi_configs:
            if not self.roi_configs[roi_id].detect_occupancy:
                continue
            observed = self.roi_configs[roi_id].observed_classes
            inside_ids = [
                tid for tid, inside in self.zone_state[roi_id].items()
                if inside and tid in self.entity_states
                and self.entity_states[tid].object_class in observed
            ]
            class_counts: dict[str, int] = {}
            max_dwell = 0.0
            for tid in inside_ids:
                state = self.entity_states.get(tid)
                if state is None:
                    continue
                cls = state.object_class
                class_counts[cls] = class_counts.get(cls, 0) + 1
                entry_start = state.roi_entry_started_at.get(roi_id)
                if entry_start:
                    dwell = (timestamp - entry_start).total_seconds()
                    if dwell > max_dwell:
                        max_dwell = dwell
            self.snapshots.append(
                OccupancySnapshot(
                    roi_id=roi_id,
                    captured_at=timestamp,
                    frame_number=self._frame_index,
                    count_inside=len(inside_ids),
                    count_outside=total_tracked - len(inside_ids),
                    track_ids_inside=inside_ids,
                    object_class_counts=class_counts,
                )
            )
            # ── Rule engine: emit alert events for matching alert_rules ──
            rules = self._alert_rules_by_roi.get(roi_id) or []
            if rules:
                from src.services.rule_evaluator import RuleEvaluator
                evalr = RuleEvaluator(roi_id, rules)
                triggered = evalr.evaluate(
                    timestamp=timestamp,
                    frame_index=self._frame_index,
                    class_counts=class_counts,
                    current_occupancy=len(inside_ids),
                    last_dwell_seconds=max_dwell if max_dwell > 0 else None,
                )
                if triggered:
                    print(f"[DEBUG] CounterEngine._take_snapshot: {len(triggered)} rule events triggered for roi={roi_id}", flush=True)
                    self.events.extend(triggered)
        print(f"[DEBUG] CounterEngine._take_snapshot: added {len(self.roi_configs)} snapshots, total={len(self.snapshots)}", flush=True)

    def get_tracked_entities(self) -> list[TrackedEntityRecord]:
        print(f"[DEBUG] CounterEngine.get_tracked_entities: ENTRY n_entities={len(self.entity_states)}", flush=True)
        result = [
            TrackedEntityRecord(
                track_id=state.track_id,
                first_seen_at=state.first_seen_at,
                last_seen_at=state.last_seen_at,
                first_seen_frame=state.first_seen_frame,
                last_seen_frame=state.last_seen_frame,
                object_class=state.object_class,
            )
            for state in self.entity_states.values()
        ]
        print(f"[DEBUG] CounterEngine.get_tracked_entities: returning {len(result)} records", flush=True)
        return result

    def get_unique_inside_count(self) -> int:
        unique_inside = {
            track_id
            for track_id, state in self.entity_states.items()
            if any(state.inside_rois.values())
        }
        return len(unique_inside)

    def get_roi_unique_count(self, roi_id: str, direction: str) -> int:
        return len(self.zone_unique_tracks[roi_id][direction])


def _open_video_writer(output_path: Path, fps: float, size: tuple[int, int]) -> cv2.VideoWriter:
    codecs = ("avc1", "H264", "mp4v")
    for codec in codecs:
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*codec),
            fps,
            size,
        )
        if writer.isOpened():
            print(f"[DEBUG] _open_video_writer: using codec={codec} path={output_path}", flush=True)
            return writer
        writer.release()
        print(f"[DEBUG] _open_video_writer: codec={codec} not available", flush=True)
    raise RuntimeError("No compatible video codec available for browser playback")


# ── Model cache (singleton lazy) ────────────────────────────────────────────
_model_instance = None  # type: ignore


def _get_model():
    global _model_instance
    if _model_instance is None:
        print(f"[DEBUG] _get_model: loading model from {YOLO_MODEL_PATH}", flush=True)
        from ultralytics import YOLO  # import lazy: torch no se carga hasta aca

        path = Path(YOLO_MODEL_PATH)
        if not path.exists():
            raise FileNotFoundError(
                f"Modelo YOLO no encontrado en {YOLO_MODEL_PATH}. "
                f"Asegurate de tener el .pt en src/inference/"
            )
        _model_instance = YOLO(path)
        print(f"[DEBUG] _get_model: model loaded successfully", flush=True)
    else:
        print(f"[DEBUG] _get_model: returning cached model instance", flush=True)
    return _model_instance


def _draw_multiline_panel(frame: np.ndarray, lines: list[str]) -> None:
    if not lines:
        return

    panel_height = 18 + 26 * len(lines)
    overlay = frame.copy()
    cv2.rectangle(overlay, (12, 12), (420, panel_height), (22, 28, 36), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    for idx, text in enumerate(lines):
        y = 38 + (idx * 24)
        cv2.putText(
            frame,
            text,
            (24, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def _annotate_frame(
    frame: np.ndarray,
    engine: CounterEngine,
    roi_configs: list[ROIConfig],
    boxes: np.ndarray | None,
    ids: np.ndarray | None,
) -> np.ndarray:
    print(f"[DEBUG] _annotate_frame: ENTRY boxes={boxes is not None} ids={ids is not None} len_rois={len(roi_configs)}", flush=True)
    annotated = frame.copy()

    for roi in roi_configs:
        pts = np.array(roi.polygon, dtype=np.int32)
        overlay = annotated.copy()
        cv2.fillPoly(overlay, [pts], (15, 118, 110))
        cv2.addWeighted(overlay, 0.12, annotated, 0.88, 0, annotated)
        cv2.polylines(annotated, [pts], isClosed=True, color=(15, 118, 110), thickness=2)

        inside_now = sum(1 for inside in engine.zone_state[roi.id].values() if inside)
        entered_unique = engine.get_roi_unique_count(roi.id, "entry")
        exited_unique = engine.get_roi_unique_count(roi.id, "exit")
        label = (
            f"{roi.name} | in:{inside_now} "
            f"entered:{entered_unique} "
            f"exited:{exited_unique}"
        )
        anchor = pts[0]
        text_pos = (int(anchor[0]), max(24, int(anchor[1]) - 8))
        cv2.putText(
            annotated,
            label,
            text_pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            label,
            text_pos,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (15, 118, 110),
            1,
            cv2.LINE_AA,
        )

    if boxes is not None and ids is not None:
        for bbox, track_id in zip(boxes, ids):
            x1, y1, x2, y2 = map(int, bbox)
            state = engine.entity_states.get(int(track_id))
            inside_rois = []
            if state:
                inside_rois = [
                    roi.name
                    for roi in roi_configs
                    if state.inside_rois.get(roi.id, False)
                ]

            box_color = (22, 163, 74) if inside_rois else (59, 130, 246)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)
            label = f"ID {int(track_id)}"
            if inside_rois:
                label += " | " + ",".join(inside_rois[:2])
            cv2.putText(
                annotated,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

    total_inside = engine.get_unique_inside_count()
    total_entered = sum(engine.get_roi_unique_count(roi.id, "entry") for roi in roi_configs)
    total_exited = sum(engine.get_roi_unique_count(roi.id, "exit") for roi in roi_configs)
    lines = [
        f"Tracked IDs: {len(engine.entity_states)}",
        f"People currently inside ROI: {total_inside}",
        f"Unique ROI entries: {total_entered}",
        f"Unique ROI exits: {total_exited}",
    ]
    for roi in roi_configs[:4]:
        lines.append(
            f"{roi.name}: Entered {engine.get_roi_unique_count(roi.id, 'entry')} | Exited {engine.get_roi_unique_count(roi.id, 'exit')}"
        )
    _draw_multiline_panel(annotated, lines)

    return annotated


class AnalyticsService:
    def __init__(
        self,
        config: VideoSourceConfig,
        roi_configs: list[ROIConfig],
        persist: bool = False,
        session_repo: Optional[SessionRepository] = None,
        entity_repo: Optional[TrackedEntityRepository] = None,
        snapshot_repo: Optional[OccupancySnapshotRepository] = None,
        zone_repo: Optional[ZoneEventRepository] = None,
    ):
        self.config = config
        self.roi_configs = roi_configs
        self.provider: FrameProvider = VideoSourceFactory.create(config)
        self.persist = persist
        if persist:
            self._session_repo = session_repo or SessionRepository()
            self._entity_repo = entity_repo or TrackedEntityRepository()
            self._snapshot_repo = snapshot_repo or OccupancySnapshotRepository()
            self._zone_repo = zone_repo or ZoneEventRepository()
        else:
            self._session_repo = None
            self._entity_repo = None
            self._snapshot_repo = None
            self._zone_repo = None

    def process(
        self,
        write_video: bool = True,
        extra_analysis: Optional[dict] = None,
        tracking_classes: Optional[list[int]] = None,
        frame_skip: int = 1,
        max_seconds: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> SessionResult:
        print(f"[DEBUG] AnalyticsService.process: ENTRY write_video={write_video} tracking_classes={tracking_classes} frame_skip={frame_skip} max_seconds={max_seconds} provider={type(self.provider).__name__}", flush=True)
        model = _get_model()
        # Load active alert_rules per ROI for the rule engine
        alert_rules_by_roi: dict[str, list[dict]] = {}
        try:
            from src.repositories.alert_rule_repo import AlertRuleRepository
            alert_repo = AlertRuleRepository()
            for roi in self.roi_configs:
                alert_rules_by_roi[roi.id] = alert_repo.list_active(roi.id)
        except Exception as e:
            print(f"[WARN] AnalyticsService.process: failed to load alert rules: {e}", flush=True)
        engine = CounterEngine(self.roi_configs, alert_rules_by_roi=alert_rules_by_roi)

        out_path = None
        writer = None

        OUTPUT_PATH = Path(OUTPUT_DIR)
        REPORTS_PATH = Path(REPORTS_DIR)

        started_at = datetime.now()
        frame_index = 0
        processed_frames = 0
        timestamp_mode = TimestampMode.REALTIME if self.provider.is_live else TimestampMode.FRAME_BASED
        fps = self.provider.get_fps() or 30.0
        total_source_frames = self.provider.get_total_frames()
        total_seconds_target = None
        if max_seconds is not None:
            total_seconds_target = float(max_seconds)
        elif total_source_frames and fps > 0:
            total_seconds_target = total_source_frames / fps

        try:
            while True:
                frame = self.provider.next_frame()
                if frame is None:
                    print(f"[DEBUG] AnalyticsService.process: provider.next_frame() returned None, breaking loop", flush=True)
                    break

                # Frame skip: skip N-1 frames between processed frames
                if frame_index % frame_skip != 0:
                    frame_index += 1
                    continue

                if frame_index % 50 == 0:
                    print(f"[DEBUG] AnalyticsService.process: frame_index={frame_index} processed_frames={processed_frames}", flush=True)

                if write_video and writer is None:
                    h, w = frame.shape[:2]
                    out_path = OUTPUT_PATH / f"{self.config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    print(f"[DEBUG] AnalyticsService.process: initializing VideoWriter -> {out_path} fps={fps} size=({w},{h})", flush=True)
                    writer = _open_video_writer(out_path, fps, (w, h))

                # Use tracking_classes if provided, default to [0] (person only) for backward compat
                track_classes = tracking_classes if tracking_classes is not None else [0]
                results = model.track(
                    frame,
                    persist=True,
                    verbose=False,
                    classes=track_classes,
                    conf=0.3,
                    tracker="bytetrack.yaml",
                )

                result = results[0]
                boxes = None
                ids = None
                class_ids = None
                if result.boxes is not None and result.boxes.id is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    ids = result.boxes.id.cpu().numpy().astype(int)
                    if result.boxes.cls is not None:
                        class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    print(f"[DEBUG] AnalyticsService.process: YOLO tracking -> {len(boxes)} detections with ids", flush=True)

                    for det_idx, (bbox, track_id) in enumerate(zip(boxes, ids)):
                        x1, y1, x2, y2 = bbox
                        center = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                        foot_left = (x1, y2)
                        foot_right = (x2, y2)
                        ts = datetime.now() if timestamp_mode == TimestampMode.REALTIME else started_at
                        cls_id = int(class_ids[det_idx]) if class_ids is not None else 0
                        object_class = _YOLO_ID_TO_CLASS.get(cls_id, f"class_{cls_id}")
                        engine.update(frame_index, int(track_id), center, foot_left, foot_right, ts, object_class)
                    print(f"[DEBUG] AnalyticsService.process: after engine.update() total_events={len(engine.events)}", flush=True)
                else:
                    print(f"[DEBUG] AnalyticsService.process: YOLO returned no tracked objects (boxes={result.boxes is not None}, ids={result.boxes is not None and result.boxes.id is not None})", flush=True)

                if writer:
                    writer.write(
                        _annotate_frame(frame, engine, self.roi_configs, boxes, ids)
                    )

                frame_index += 1
                processed_frames += 1
                elapsed_seconds = frame_index / fps if fps > 0 else float(processed_frames)

                # Time limit in source-video seconds
                if max_seconds is not None and elapsed_seconds >= max_seconds:
                    print(f"[DEBUG] AnalyticsService.process: reached max_seconds={max_seconds}, breaking", flush=True)
                    break

                # Progress callback
                if progress_callback:
                    total_frames_for_progress = int(total_seconds_target * fps) if total_seconds_target is not None and fps > 0 else total_source_frames
                    progress_callback(processed_frames, total_frames_for_progress, elapsed_seconds, total_seconds_target)
        finally:
            print(f"[DEBUG] AnalyticsService.process: ENTERING finally block", flush=True)
            if writer:
                print(f"[DEBUG] AnalyticsService.process: releasing writer", flush=True)
                writer.release()
                # Re-encode FMP4 → H.264 via bundled FFmpeg so browsers can play
                if out_path:
                    try:
                        from imageio_ffmpeg import get_ffmpeg_exe
                        import subprocess
                        ffmpeg = get_ffmpeg_exe()
                        h264_path = out_path.with_name(out_path.stem + "_h264" + out_path.suffix)
                        subprocess.run(
                            [ffmpeg, "-y", "-i", str(out_path),
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                             "-c:a", "aac", str(h264_path)],
                            capture_output=True, timeout=120,
                        )
                        if h264_path.exists():
                            out_path.unlink(missing_ok=True)          # remove FMP4
                            h264_path.rename(out_path)                # replace with H.264
                            print(f"[DEBUG] Re-encoded to H.264: {out_path}", flush=True)
                    except Exception as e:
                        print(f"[WARN] FFmpeg re-encode failed, keeping original: {e}", flush=True)
            print(f"[DEBUG] AnalyticsService.process: releasing provider", flush=True)
            self.provider.release()
            print(f"[DEBUG] AnalyticsService.process: EXIT finally block", flush=True)

        ended_at = datetime.now()
        print(f"[DEBUG] AnalyticsService.process: loop ended, frame_index={frame_index} processed_frames={processed_frames} events={len(engine.events)}", flush=True)
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
        print(f"[DEBUG] AnalyticsService.process: SessionResult created id={session_result.id}", flush=True)

        if self.persist and self._session_repo:
            session_id = self._persist_session(session_result)
            session_result.id = str(session_id)
            print(f"[DEBUG] AnalyticsService.process: persisted session_id={session_id}", flush=True)
            # Compute derived metrics from ZoneEvents
            try:
                MetricsService().compute(session_id)
                print(f"[DEBUG] AnalyticsService.process: MetricSnapshot computed for session_id={session_id}", flush=True)
            except Exception as e:
                print(f"[ERROR] AnalyticsService.process: MetricsService.compute failed: {e}", flush=True)

        print(f"[DEBUG] AnalyticsService.process: returning SessionResult id={session_result.id}", flush=True)
        return session_result

    def _persist_session(self, session_result: SessionResult) -> UUID:
        print(f"[DEBUG] AnalyticsService._persist_session: ENTRY", flush=True)
        session_id = self._session_repo.create_session(session_result)
        print(f"[DEBUG] AnalyticsService._persist_session: session created, persisting entities/snapshots/events in parallel", flush=True)
        # Las 3 operaciones son independientes → corren en paralelo
        # 3 threads independientes con 3 connections distintas del pool
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="persist") as executor:
            f_entities = executor.submit(
                self._entity_repo.save_all,
                session_id, session_result.tracked_entities,
            )
            f_snapshots = executor.submit(
                self._snapshot_repo.create_batch,
                session_id, session_result.occupancy_snapshots,
            )
            f_events = executor.submit(
                self._zone_repo.create_batch,
                session_id, session_result.zone_events,
            )
            # Esperar y propagar excepciones (fail fast)
            for future in (f_entities, f_snapshots, f_events):
                future.result()
        print(f"[DEBUG] AnalyticsService._persist_session: parallel persist complete", flush=True)
        return session_id
