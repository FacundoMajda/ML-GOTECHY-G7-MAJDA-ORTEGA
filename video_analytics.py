from __future__ import annotations

import base64
import html
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent
CONTENT_DIR = BASE_DIR / "sample_data" / "content"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = BASE_DIR / "reports"


@dataclass(frozen=True)
class RoiZone:
    name: str
    polygon: list[list[int]]
    count_label: str
    count_only_full_passage: bool = False
    expected_direction: Optional[str] = None


@dataclass(frozen=True)
class VideoConfig:
    key: str
    title: str
    description: str
    path_candidates: list[str]
    roi_polygon: list[list[int]]
    flow_start: list[int]
    flow_end: list[int]
    positive_label: str
    negative_label: str
    roi_zones: Optional[list[RoiZone]] = None
    roi_label: str = "ROI"
    count_only_full_passage: bool = False
    tracking_point: str = "foot"


@dataclass
class EventRecord:
    frame_index: int
    track_id: int
    event_type: str
    flow_label: Optional[str]


@dataclass
class StatsSummary:
    video_key: str
    video_title: str
    source_path: str
    processed_at: str
    frames_processed: int
    fps: float
    roi_entries: int
    roi_exits: int
    total_roi_passers: int
    flow_positive: int
    flow_negative: int
    positive_label: str
    negative_label: str
    count_only_full_passage: bool
    zone_counts: dict[str, int]
    extra_analysis_requested: bool = False
    extra_analysis_target: str = ""
    output_video: Optional[str] = None
    report_path: Optional[str] = None
    preview_path: Optional[str] = None
    event_log: list[EventRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["event_log"] = [asdict(event) for event in self.event_log]
        return payload


VIDEO_CONFIGS: dict[str, VideoConfig] = {
    "stair_before": VideoConfig(
        key="stair_before",
        title="Escalera - Antes",
        description="Escena de escalera original para contar subidas y bajadas.",
        path_candidates=[
            str(CONTENT_DIR / "output_h264_antes.mp4"),
            "/content/sample_data/output_h264_antes.mp4",
        ],
        roi_polygon=[
            [1824, 500],
            [1904, 436],
            [1122, 332],
            [984, 366],
        ],
        roi_zones=None,
        flow_start=[1864, 468],
        flow_end=[1053, 349],
        positive_label="bajando",
        negative_label="subiendo",
        roi_label="Escalera",
        count_only_full_passage=False,
        tracking_point="foot",
    ),
    "mall": VideoConfig(
        key="mall",
        title="Mall - Puerta giratoria",
        description="Conteo de gente que entra o sale del mall a traves de la puerta.",
        path_candidates=[
            str(CONTENT_DIR / "mall.mp4"),
            "/content/sample_data/mall.mp4",
        ],
        roi_polygon=[
            [578, 230],
            [742, 246],
            [732, 446],
            [584, 450],
        ],
        roi_zones=[
            RoiZone(
                name="entrada",
                polygon=[
                    [578, 230],
                    [742, 246],
                    [732, 446],
                    [584, 450],
                ],
                count_label="entrada",
                count_only_full_passage=True,
                expected_direction="down",
            ),
            RoiZone(
                name="salida",
                polygon=[
                    [794, 218],
                    [1010, 218],
                    [1018, 442],
                    [796, 448],
                ],
                count_label="salida",
                count_only_full_passage=True,
                expected_direction="up",
            ),
        ],
        flow_start=[690, 539],
        flow_end=[696, 494],
        positive_label="salida",
        negative_label="entrada",
        roi_label="Puerta",
        count_only_full_passage=True,
        tracking_point="head",
    ),
}


def list_video_options() -> list[dict]:
    options = []
    for key, config in VIDEO_CONFIGS.items():
        options.append(
            {
                "key": key,
                "title": config.title,
                "description": config.description,
                "path": resolve_video_path(config),
                "roi_polygon": config.roi_polygon,
                "roi_zones": [
                    {"name": zone.name, "polygon": zone.polygon, "count_label": zone.count_label}
                    for zone in (config.roi_zones or [])
                ],
                "positive_label": config.positive_label,
                "negative_label": config.negative_label,
            }
        )
    return options


def resolve_video_path(config: VideoConfig) -> str:
    for candidate in config.path_candidates:
        if Path(candidate).exists():
            return str(Path(candidate))
    return config.path_candidates[0]


class CounterEngine:
    def __init__(self, config: VideoConfig, history_len: int = 10):
        self.config = config
        self.use_multi_zone = bool(config.roi_zones)
        self.roi_polygon = np.array(config.roi_polygon, dtype=np.int32)
        self.roi_zones = config.roi_zones or [
            RoiZone(
                name=config.roi_label.lower(),
                polygon=config.roi_polygon,
                count_label=config.roi_label,
                count_only_full_passage=config.count_only_full_passage,
            )
        ]
        self.zone_polygons = {
            zone.name: np.array(zone.polygon, dtype=np.int32)
            for zone in self.roi_zones
        }
        self.axis_start = np.array(config.flow_start, dtype=np.float32)
        self.axis_end = np.array(config.flow_end, dtype=np.float32)
        self.history_len = history_len
        self.track_state: dict[int, bool] = {}
        self.positions: dict[int, tuple[float, float]] = {}
        self.direction_history: dict[int, list[str]] = {}
        self.seen_inside_ids: set[int] = set()
        self.roi_entries = 0
        self.roi_exits = 0
        self.total_roi_passers = 0
        self.flow_positive = 0
        self.flow_negative = 0
        self.events: list[EventRecord] = []
        self.pending_passages: dict[int, Optional[str]] = {}
        self.zone_state: dict[str, dict[int, bool]] = {zone.name: {} for zone in self.roi_zones}
        self.zone_pending: dict[str, set[int]] = {zone.name: set() for zone in self.roi_zones}
        self.zone_counts: dict[str, int] = {zone.count_label: 0 for zone in self.roi_zones}
        self.track_vertical_direction: dict[int, str] = {}

    def is_inside(self, point: tuple[float, float]) -> bool:
        if self.use_multi_zone:
            return any(
                cv2.pointPolygonTest(self.zone_polygons[zone.name], point, measureDist=False) >= 0
                for zone in self.roi_zones
            )
        return cv2.pointPolygonTest(self.roi_polygon, point, measureDist=False) >= 0

    def zone_membership(self, point: tuple[float, float]) -> dict[str, bool]:
        return {
            zone.name: cv2.pointPolygonTest(self.zone_polygons[zone.name], point, measureDist=False) >= 0
            for zone in self.roi_zones
        }

    def classify_direction(
        self,
        prev_point: tuple[float, float],
        curr_point: tuple[float, float],
    ) -> str:
        axis_vector = self.axis_end - self.axis_start
        movement = np.array(curr_point, dtype=np.float32) - np.array(prev_point, dtype=np.float32)
        projection = float(np.dot(movement, axis_vector))
        if projection > 0:
            return self.config.positive_label
        if projection < 0:
            return self.config.negative_label
        return "quieto"

    @staticmethod
    def classify_vertical_direction(
        prev_point: tuple[float, float],
        curr_point: tuple[float, float],
    ) -> str:
        delta_y = float(curr_point[1] - prev_point[1])
        if delta_y > 0:
            return "down"
        if delta_y < 0:
            return "up"
        return "quieto"

    def update(
        self,
        frame_index: int,
        track_id: int,
        inside: bool,
        center: tuple[float, float],
        zone_hits: Optional[dict[str, bool]] = None,
    ) -> None:
        if self.use_multi_zone:
            self.track_state[track_id] = inside
            self.positions[track_id] = center
            if zone_hits:
                self._update_zone_counts(frame_index, track_id, zone_hits)
            return

        prev_inside = self.track_state.get(track_id)
        prev_position = self.positions.get(track_id)

        direction: Optional[str] = None
        if prev_position is not None:
            direction = self.classify_direction(prev_position, center)
            vertical_direction = self.classify_vertical_direction(prev_position, center)
            if vertical_direction != "quieto":
                self.track_vertical_direction[track_id] = vertical_direction
            if direction != "quieto":
                hist = self.direction_history.setdefault(track_id, [])
                hist.append(direction)
                if len(hist) > self.history_len:
                    hist.pop(0)

        if prev_inside != inside:
            history = self.direction_history.get(track_id, [])
            if history:
                dominant_direction = max(set(history), key=history.count)
            else:
                dominant_direction = direction

            if prev_inside is False and inside:
                self.roi_entries += 1
                if self.config.count_only_full_passage:
                    self.pending_passages[track_id] = dominant_direction
                else:
                    if track_id not in self.seen_inside_ids:
                        self.seen_inside_ids.add(track_id)
                        self.total_roi_passers += 1
                    if dominant_direction == self.config.positive_label:
                        self.flow_positive += 1
                    elif dominant_direction == self.config.negative_label:
                        self.flow_negative += 1
                self.events.append(
                    EventRecord(
                        frame_index=frame_index,
                        track_id=track_id,
                        event_type="entered_roi",
                        flow_label=dominant_direction,
                    )
                )
            elif prev_inside is True and not inside:
                self.roi_exits += 1
                if self.config.count_only_full_passage:
                    passage_direction = self.pending_passages.pop(track_id, dominant_direction)
                    if passage_direction in (self.config.positive_label, self.config.negative_label):
                        self.total_roi_passers += 1
                        if passage_direction == self.config.positive_label:
                            self.flow_positive += 1
                        else:
                            self.flow_negative += 1
                self.events.append(
                    EventRecord(
                        frame_index=frame_index,
                        track_id=track_id,
                        event_type="exited_roi",
                        flow_label=dominant_direction,
                    )
                )

        self.track_state[track_id] = inside
        self.positions[track_id] = center
        if zone_hits:
            self._update_zone_counts(frame_index, track_id, zone_hits)

    def _update_zone_counts(
        self,
        frame_index: int,
        track_id: int,
        zone_hits: dict[str, bool],
    ) -> None:
        for zone in self.roi_zones:
            current_inside = zone_hits.get(zone.name, False)
            zone_state = self.zone_state[zone.name]
            prev_inside = zone_state.get(track_id)

            if prev_inside != current_inside:
                if prev_inside is False and current_inside:
                    if zone.count_only_full_passage:
                        self.zone_pending[zone.name].add(track_id)
                    else:
                        self.zone_counts[zone.count_label] += 1
                elif prev_inside is True and not current_inside:
                    if zone.count_only_full_passage and track_id in self.zone_pending[zone.name]:
                        track_direction = self.track_vertical_direction.get(track_id, "quieto")
                        if zone.expected_direction in (None, track_direction):
                            self.zone_counts[zone.count_label] += 1
                            self.total_roi_passers += 1
                            self.events.append(
                                EventRecord(
                                    frame_index=frame_index,
                                    track_id=track_id,
                                    event_type=f"completed_{zone.name}",
                                    flow_label=zone.count_label,
                                )
                            )
                        self.zone_pending[zone.name].remove(track_id)

            zone_state[track_id] = current_inside

        if self.config.key == "mall":
            self.flow_negative = self.zone_counts.get("entrada", 0)
            self.flow_positive = self.zone_counts.get("salida", 0)
            self.total_roi_passers = sum(self.zone_counts.values())

    def cleanup_missing(self, active_ids: set[int]) -> None:
        for store in (self.track_state, self.positions, self.direction_history):
            for track_id in list(store.keys()):
                if track_id not in active_ids:
                    del store[track_id]
        for track_id in list(self.pending_passages.keys()):
            if track_id not in active_ids:
                del self.pending_passages[track_id]
        for zone in self.roi_zones:
            zone_state = self.zone_state[zone.name]
            for track_id in list(zone_state.keys()):
                if track_id not in active_ids:
                    del zone_state[track_id]
            self.zone_pending[zone.name].intersection_update(active_ids)
        for track_id in list(self.track_vertical_direction.keys()):
            if track_id not in active_ids:
                del self.track_vertical_direction[track_id]


def _foot_point(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x1, _, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


def _head_point(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x1, y1, x2, _ = bbox
    return ((x1 + x2) / 2.0, y1)


def _center_point(bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _tracking_point_for_config(
    config: VideoConfig,
    bbox: tuple[float, float, float, float],
) -> tuple[float, float]:
    if config.tracking_point == "head":
        return _head_point(bbox)
    return _foot_point(bbox)


def _annotate_frame(
    frame: np.ndarray,
    config: VideoConfig,
    engine: CounterEngine,
    visible_tracks: list[dict],
) -> np.ndarray:
    annotated = frame.copy()
    zones = config.roi_zones or [
        RoiZone(
            name=config.roi_label.lower(),
            polygon=config.roi_polygon,
            count_label=config.roi_label,
            count_only_full_passage=config.count_only_full_passage,
        )
    ]
    palette = [(0, 0, 255), (0, 140, 255), (0, 180, 180), (180, 0, 180)]
    for idx, zone in enumerate(zones):
        color = palette[idx % len(palette)]
        roi_polygon = np.array(zone.polygon, dtype=np.int32)
        cv2.polylines(annotated, [roi_polygon], isClosed=True, color=color, thickness=3)
        x, y = zone.polygon[0]
        cv2.putText(
            annotated,
            zone.count_label.upper(),
            (x, max(30, y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )

    for track in visible_tracks:
        x1, y1, x2, y2 = track["bbox"]
        color = (0, 200, 0) if track["inside"] else (0, 0, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"ID:{track['track_id']}"
        if track["direction"] and track["direction"] != "quieto":
            label += f" {track['direction']}"
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    if config.roi_zones:
        stats = [
            f"SALIDA: {engine.zone_counts.get('salida', engine.flow_positive)}",
            f"ENTRADA: {engine.zone_counts.get('entrada', engine.flow_negative)}",
            f"TOTAL CRUCES ROI: {sum(engine.zone_counts.values())}",
        ]
    elif config.count_only_full_passage:
        stats = [
            f"{config.positive_label.upper()}: {engine.flow_positive}",
            f"{config.negative_label.upper()}: {engine.flow_negative}",
            f"CRUCES COMPLETOS ROI: {engine.total_roi_passers}",
        ]
    else:
        stats = [
            f"{config.positive_label.upper()}: {engine.flow_positive}",
            f"{config.negative_label.upper()}: {engine.flow_negative}",
            f"ENTRAN ROI: {engine.roi_entries}",
            f"SALEN ROI: {engine.roi_exits}",
            f"TOTAL PERSONAS ROI: {engine.total_roi_passers}",
        ]
    for idx, text in enumerate(stats):
        x = 20
        y = 40 + idx * 38
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.rectangle(annotated, (x - 6, y - th - 6), (x + tw + 6, y + 8), (255, 255, 255), -1)
        cv2.putText(annotated, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)

    return annotated


def _encode_preview(frame: np.ndarray, max_width: int = 960) -> str:
    preview = frame.copy()
    h, w = preview.shape[:2]
    if w > max_width:
        scale = max_width / float(w)
        preview = cv2.resize(preview, (int(w * scale), int(h * scale)))
    ok, encoded = cv2.imencode(".jpg", preview)
    if not ok:
        return ""
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def process_video(
    video_key: str,
    *,
    model_path: str = "yolo11n.pt",
    confidence: float = 0.3,
    write_video: bool = True,
    extra_analysis_requested: bool = False,
    extra_analysis_target: str = "",
) -> StatsSummary:
    if video_key not in VIDEO_CONFIGS:
        raise KeyError(f"Video desconocido: {video_key}")

    config = VIDEO_CONFIGS[video_key]
    source_path = resolve_video_path(config)
    if not Path(source_path).exists():
        raise FileNotFoundError(
            f"No se encontro el video para '{video_key}'. Revise estas rutas: {config.path_candidates}"
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    cap = cv2.VideoCapture(source_path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {source_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_video_path = OUTPUT_DIR / f"{video_key}_{timestamp}.mp4"

    writer = None
    if write_video:
        writer = cv2.VideoWriter(
            str(output_video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError("No se pudo abrir el VideoWriter para el video de salida.")

    model = YOLO(model_path)
    engine = CounterEngine(config)
    frame_index = 0
    preview_frame: Optional[np.ndarray] = None

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            results = model.track(
                frame,
                persist=True,
                verbose=False,
                classes=[0],
                conf=confidence,
                tracker="bytetrack.yaml",
            )

            visible_tracks = []
            active_ids: set[int] = set()
            result = results[0]
            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                ids = result.boxes.id.cpu().numpy().astype(int)
                for bbox, track_id in zip(boxes, ids):
                    bbox_tuple = tuple(map(float, bbox.tolist()))
                    tracking_point = _tracking_point_for_config(config, bbox_tuple)
                    center = _center_point(bbox_tuple)
                    inside = engine.is_inside(tracking_point)
                    zone_hits = engine.zone_membership(tracking_point)
                    engine.update(frame_index, int(track_id), inside, center, zone_hits=zone_hits)
                    direction = None
                    if int(track_id) in engine.direction_history and engine.direction_history[int(track_id)]:
                        hist = engine.direction_history[int(track_id)]
                        direction = max(set(hist), key=hist.count)
                    active_ids.add(int(track_id))
                    visible_tracks.append(
                        {
                            "track_id": int(track_id),
                            "bbox": tuple(map(int, bbox_tuple)),
                            "inside": inside,
                            "direction": direction,
                        }
                    )

            engine.cleanup_missing(active_ids)
            annotated = _annotate_frame(frame, config, engine, visible_tracks)

            if preview_frame is None and visible_tracks:
                preview_frame = annotated.copy()

            if writer is not None:
                writer.write(annotated)

            frame_index += 1
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    report_path = REPORTS_DIR / f"{video_key}_{timestamp}.html"
    preview_path = REPORTS_DIR / f"{video_key}_{timestamp}_preview.jpg"
    if preview_frame is not None:
        cv2.imwrite(str(preview_path), preview_frame)
    else:
        preview_path = None

    summary = StatsSummary(
        video_key=config.key,
        video_title=config.title,
        source_path=str(source_path),
        processed_at=datetime.now().isoformat(timespec="seconds"),
        frames_processed=frame_index,
        fps=float(fps),
        roi_entries=engine.roi_entries,
        roi_exits=engine.roi_exits,
        total_roi_passers=engine.total_roi_passers,
        flow_positive=engine.flow_positive,
        flow_negative=engine.flow_negative,
        positive_label=config.positive_label,
        negative_label=config.negative_label,
        count_only_full_passage=config.count_only_full_passage,
        zone_counts=engine.zone_counts,
        extra_analysis_requested=extra_analysis_requested,
        extra_analysis_target=extra_analysis_target.strip(),
        output_video=str(output_video_path) if writer is not None else None,
        report_path=str(report_path),
        preview_path=str(preview_path) if preview_path else None,
        event_log=engine.events,
    )
    report_path.write_text(generate_report_html(summary), encoding="utf-8")
    return summary


def process_named_video(
    video_key: str,
    write_video: bool = True,
    extra_analysis_requested: bool = False,
    extra_analysis_target: str = "",
) -> StatsSummary:
    return process_video(
        video_key,
        write_video=write_video,
        extra_analysis_requested=extra_analysis_requested,
        extra_analysis_target=extra_analysis_target,
    )


def generate_report_html(summary: StatsSummary) -> str:
    preview_img = ""
    if summary.preview_path and Path(summary.preview_path).exists():
        encoded = base64.b64encode(Path(summary.preview_path).read_bytes()).decode("ascii")
        preview_img = (
            '<div class="preview">'
            f'<img alt="preview" src="data:image/jpeg;base64,{encoded}" />'
            "</div>"
        )

    events_rows = "\n".join(
        (
            "<tr>"
            f"<td>{event.frame_index}</td>"
            f"<td>{event.track_id}</td>"
            f"<td>{html.escape(event.event_type)}</td>"
            f"<td>{html.escape(event.flow_label or '-')}</td>"
            "</tr>"
        )
        for event in summary.event_log[-30:]
    )
    if not events_rows:
        events_rows = '<tr><td colspan="4">Sin eventos registrados.</td></tr>'

    extra_analysis_html = (
        f"""
      <div class="panel">
        <h2>Análisis adicional solicitado</h2>
        <p><strong>Pedido:</strong> {html.escape(summary.extra_analysis_target)}</p>
        <p class="muted">Este pedido quedó registrado en la interfaz, pero el modelo actual solo cuenta personas. Para detectar atributos como gorro habría que sumar un modelo o clasificador adicional.</p>
      </div>
"""
        if summary.extra_analysis_requested and summary.extra_analysis_target.strip()
        else ""
    )

    output_video_line = (
        f'<p><strong>Video anotado:</strong> {html.escape(summary.output_video)}</p>'
        if summary.output_video
        else ""
    )

    if summary.zone_counts:
        roi_stats_html = "".join(
            f"""
      <div class="stat">
        <div class="label">{html.escape(label)}</div>
        <div class="value">{value}</div>
      </div>
"""
            for label, value in summary.zone_counts.items()
        ) + f"""
      <div class="stat">
        <div class="label">Total cruces ROI</div>
        <div class="value">{sum(summary.zone_counts.values())}</div>
      </div>
"""
    elif summary.count_only_full_passage:
        roi_stats_html = f"""
      <div class="stat">
        <div class="label">Cruces completos ROI</div>
        <div class="value">{summary.total_roi_passers}</div>
      </div>
"""
    else:
        roi_stats_html = f"""
      <div class="stat">
        <div class="label">Entradas al ROI</div>
        <div class="value">{summary.roi_entries}</div>
      </div>
      <div class="stat">
        <div class="label">Salidas del ROI</div>
        <div class="value">{summary.roi_exits}</div>
      </div>
      <div class="stat">
        <div class="label">Personas que pasaron por ROI</div>
        <div class="value">{summary.total_roi_passers}</div>
      </div>
"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reporte {html.escape(summary.video_title)}</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf3;
      --ink: #1f2937;
      --muted: #6b7280;
      --accent: #0f766e;
      --accent-2: #b45309;
      --line: #eadfce;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15,118,110,0.10), transparent 26%),
        radial-gradient(circle at bottom right, rgba(180,83,9,0.14), transparent 30%),
        var(--bg);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 60px;
    }}
    .hero {{
      display: grid;
      gap: 18px;
      grid-template-columns: 1.3fr 1fr;
      align-items: center;
      margin-bottom: 24px;
    }}
    .hero-card, .panel {{
      background: rgba(255,250,243,0.94);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 22px;
      box-shadow: 0 18px 45px rgba(31,41,55,0.08);
      backdrop-filter: blur(8px);
    }}
    h1 {{ margin: 0 0 12px; font-size: 2.3rem; }}
    p {{ margin: 0 0 10px; line-height: 1.5; }}
    .muted {{ color: var(--muted); }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 24px 0;
    }}
    .stat {{
      padding: 18px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(245,239,230,0.98));
      border: 1px solid var(--line);
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 0.92rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .stat .value {{
      margin-top: 8px;
      font-size: 2rem;
      font-weight: 700;
    }}
    .preview img {{
      width: 100%;
      border-radius: 16px;
      border: 1px solid var(--line);
      display: block;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}
    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
    }}
    th {{
      color: var(--accent);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    code {{
      font-family: Consolas, monospace;
      background: rgba(15,118,110,0.08);
      padding: 2px 6px;
      border-radius: 6px;
    }}
    @media (max-width: 860px) {{
      .hero {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 1.8rem; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-card">
        <p class="muted">Reporte generado el {html.escape(summary.processed_at)}</p>
        <h1>{html.escape(summary.video_title)}</h1>
        <p>Fuente: <code>{html.escape(summary.source_path)}</code></p>
        <p>Frames procesados: <strong>{summary.frames_processed}</strong> a <strong>{summary.fps:.2f} FPS</strong>.</p>
        {output_video_line}
      </div>
      <div class="hero-card">
        {preview_img or '<p class="muted">No hubo preview disponible para este procesamiento.</p>'}
      </div>
    </section>

    <section class="stats">
      <div class="stat">
        <div class="label">{html.escape(summary.positive_label)}</div>
        <div class="value">{summary.flow_positive}</div>
      </div>
      <div class="stat">
        <div class="label">{html.escape(summary.negative_label)}</div>
        <div class="value">{summary.flow_negative}</div>
      </div>
      {roi_stats_html}
    </section>

    <section class="panel">
      <h2>Ultimos eventos</h2>
      <table>
        <thead>
          <tr>
            <th>Frame</th>
            <th>Track</th>
            <th>Evento</th>
            <th>Flujo</th>
          </tr>
        </thead>
        <tbody>
          {events_rows}
        </tbody>
      </table>
    </section>
    {extra_analysis_html}
  </div>
</body>
</html>
"""


def summary_to_json(summary: StatsSummary) -> str:
    return json.dumps(summary.to_dict(), ensure_ascii=False, indent=2)
