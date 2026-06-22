from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_PATH = Path("ml_gotechy.ipynb")
COLAB_MARKER = "COLAB_ANALYTICS_WIDGETS_V2"


def md_cell(*lines: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": list(lines),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip("\n").splitlines()],
    }


NEW_CELLS = [
    md_cell(
        "### Colab Analytics UI\n",
        "Estas celdas agregan una interfaz pensada para Google Colab: selector de video, opciones de análisis, render HTML del reporte y persistencia de estadísticas en PostgreSQL."
    ),
    code_cell(
        r'''
# COLAB_ANALYTICS_WIDGETS_V2
!pip install -q ultralytics supervision ipywidgets "psycopg[binary]"
'''
    ),
    code_cell(
        r'''
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import base64
import html
import os

import cv2
import ipywidgets as widgets
import numpy as np
import psycopg
from IPython.display import HTML, Video, display, clear_output
from ultralytics import YOLO
'''
    ),
    code_cell(
        r'''
@dataclass(frozen=True)
class NotebookRoiZone:
    name: str
    polygon: list[list[int]]
    count_label: str
    count_only_full_passage: bool = False
    expected_direction: Optional[str] = None


@dataclass(frozen=True)
class NotebookVideoConfig:
    key: str
    title: str
    description: str
    path: str
    roi_polygon: list[list[int]]
    flow_start: list[int]
    flow_end: list[int]
    positive_label: str
    negative_label: str
    roi_zones: Optional[list[NotebookRoiZone]] = None
    roi_label: str = "ROI"
    count_only_full_passage: bool = False
    tracking_point: str = "foot"


NOTEBOOK_VIDEO_CONFIGS = {
    "stair_before": NotebookVideoConfig(
        key="stair_before",
        title="Escalera - Antes",
        description="Conteo original de subidas y bajadas en la escalera.",
        path="/content/sample_data/output_h264_antes.mp4",
        roi_polygon=[
            [1824, 500],
            [1904, 436],
            [1122, 332],
            [984, 366],
        ],
        flow_start=[1864, 468],
        flow_end=[1053, 349],
        positive_label="bajando",
        negative_label="subiendo",
        roi_zones=None,
        roi_label="Escalera",
        count_only_full_passage=False,
        tracking_point="foot",
    ),
    "mall": NotebookVideoConfig(
        key="mall",
        title="Mall - Puerta giratoria",
        description="Conteo de entrada y salida usando dos ROIs independientes.",
        path="/content/sample_data/mall.mp4",
        roi_polygon=[
            [578, 230],
            [742, 246],
            [732, 446],
            [584, 450],
        ],
        flow_start=[690, 539],
        flow_end=[696, 494],
        positive_label="salida",
        negative_label="entrada",
        roi_zones=[
            NotebookRoiZone(
                name="entrada",
                polygon=[[578, 230], [742, 246], [732, 446], [584, 450]],
                count_label="entrada",
                count_only_full_passage=True,
                expected_direction="down",
            ),
            NotebookRoiZone(
                name="salida",
                polygon=[[794, 218], [1010, 218], [1018, 442], [796, 448]],
                count_label="salida",
                count_only_full_passage=True,
                expected_direction="up",
            ),
        ],
        roi_label="Puerta",
        count_only_full_passage=True,
        tracking_point="head",
    ),
}


DATABASE_URL_DEFAULT = "postgresql://neondb_owner:npg_RTjxq6eWUAN5@ep-shiny-tooth-ahz81hnv-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
'''
    ),
    code_cell(
        r'''
class NotebookCounterEngine:
    def __init__(self, config: NotebookVideoConfig, history_len: int = 10):
        self.config = config
        self.use_multi_zone = bool(config.roi_zones)
        self.roi_polygon = np.array(config.roi_polygon, dtype=np.int32)
        self.roi_zones = config.roi_zones or [
            NotebookRoiZone(
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
        self.track_vertical_direction: dict[int, str] = {}
        self.zone_state: dict[str, dict[int, bool]] = {zone.name: {} for zone in self.roi_zones}
        self.zone_pending: dict[str, set[int]] = {zone.name: set() for zone in self.roi_zones}
        self.zone_counts: dict[str, int] = {zone.count_label: 0 for zone in self.roi_zones}
        self.roi_entries = 0
        self.roi_exits = 0
        self.total_roi_passers = 0
        self.flow_positive = 0
        self.flow_negative = 0
        self.events: list[dict] = []

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

    def classify_direction(self, prev_point, curr_point) -> str:
        axis_vector = self.axis_end - self.axis_start
        movement = np.array(curr_point, dtype=np.float32) - np.array(prev_point, dtype=np.float32)
        projection = float(np.dot(movement, axis_vector))
        if projection > 0:
            return self.config.positive_label
        if projection < 0:
            return self.config.negative_label
        return "quieto"

    @staticmethod
    def classify_vertical_direction(prev_point, curr_point) -> str:
        delta_y = float(curr_point[1] - prev_point[1])
        if delta_y > 0:
            return "down"
        if delta_y < 0:
            return "up"
        return "quieto"

    def update(self, frame_index: int, track_id: int, inside: bool, center, zone_hits: Optional[dict[str, bool]] = None) -> None:
        prev_position = self.positions.get(track_id)
        direction = None
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

        if self.use_multi_zone:
            self.track_state[track_id] = inside
            self.positions[track_id] = center
            if zone_hits:
                self._update_zone_counts(frame_index, track_id, zone_hits)
            return

        prev_inside = self.track_state.get(track_id)
        if prev_inside != inside:
            history = self.direction_history.get(track_id, [])
            dominant_direction = max(set(history), key=history.count) if history else direction
            if prev_inside is False and inside:
                self.roi_entries += 1
                self.total_roi_passers += 1
                if dominant_direction == self.config.positive_label:
                    self.flow_positive += 1
                elif dominant_direction == self.config.negative_label:
                    self.flow_negative += 1
                self.events.append(
                    {
                        "frame_index": frame_index,
                        "track_id": track_id,
                        "event_type": "entered_roi",
                        "flow_label": dominant_direction,
                    }
                )
            elif prev_inside is True and not inside:
                self.roi_exits += 1
                self.events.append(
                    {
                        "frame_index": frame_index,
                        "track_id": track_id,
                        "event_type": "exited_roi",
                        "flow_label": dominant_direction,
                    }
                )

        self.track_state[track_id] = inside
        self.positions[track_id] = center

    def _update_zone_counts(self, frame_index: int, track_id: int, zone_hits: dict[str, bool]) -> None:
        for zone in self.roi_zones:
            current_inside = zone_hits.get(zone.name, False)
            zone_state = self.zone_state[zone.name]
            prev_inside = zone_state.get(track_id)

            if prev_inside != current_inside:
                if prev_inside is False and current_inside:
                    self.zone_pending[zone.name].add(track_id)
                elif prev_inside is True and not current_inside and track_id in self.zone_pending[zone.name]:
                    track_direction = self.track_vertical_direction.get(track_id, "quieto")
                    if zone.expected_direction in (None, track_direction):
                        self.zone_counts[zone.count_label] += 1
                        self.total_roi_passers += 1
                        self.events.append(
                            {
                                "frame_index": frame_index,
                                "track_id": track_id,
                                "event_type": f"completed_{zone.name}",
                                "flow_label": zone.count_label,
                            }
                        )
                    self.zone_pending[zone.name].remove(track_id)

            zone_state[track_id] = current_inside

        self.flow_negative = self.zone_counts.get("entrada", 0)
        self.flow_positive = self.zone_counts.get("salida", 0)

    def cleanup_missing(self, active_ids: set[int]) -> None:
        for store in (self.track_state, self.positions, self.direction_history, self.track_vertical_direction):
            for track_id in list(store.keys()):
                if track_id not in active_ids:
                    del store[track_id]
        for zone in self.roi_zones:
            zone_state = self.zone_state[zone.name]
            for track_id in list(zone_state.keys()):
                if track_id not in active_ids:
                    del zone_state[track_id]
            self.zone_pending[zone.name].intersection_update(active_ids)


def notebook_head_point(bbox):
    x1, y1, x2, _ = bbox
    return ((x1 + x2) / 2.0, y1)


def notebook_foot_point(bbox):
    x1, _, x2, y2 = bbox
    return ((x1 + x2) / 2.0, y2)


def notebook_center_point(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def notebook_tracking_point(config: NotebookVideoConfig, bbox):
    if config.tracking_point == "head":
        return notebook_head_point(bbox)
    return notebook_foot_point(bbox)


def notebook_annotate_frame(frame, config: NotebookVideoConfig, engine: NotebookCounterEngine, visible_tracks: list[dict]):
    annotated = frame.copy()
    zones = config.roi_zones or [
        NotebookRoiZone(
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
        cv2.putText(annotated, zone.count_label.upper(), (x, max(30, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    for track in visible_tracks:
        x1, y1, x2, y2 = track["bbox"]
        color = (0, 200, 0) if track["inside"] else (0, 0, 255)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        label = f"ID:{track['track_id']}"
        if track["direction"] and track["direction"] != "quieto":
            label += f" {track['direction']}"
        cv2.putText(annotated, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    if config.roi_zones:
        stats = [
            f"SALIDA: {engine.zone_counts.get('salida', 0)}",
            f"ENTRADA: {engine.zone_counts.get('entrada', 0)}",
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
'''
    ),
    code_cell(
        r'''
def notebook_generate_report_html(summary: dict) -> str:
    preview_html = ""
    preview_path = summary.get("preview_path")
    if preview_path and Path(preview_path).exists():
        encoded = base64.b64encode(Path(preview_path).read_bytes()).decode("ascii")
        preview_html = f'<div class="preview"><img src="data:image/jpeg;base64,{encoded}" alt="preview" /></div>'

    if summary["zone_counts"]:
        stats_html = "".join(
            f"""
            <div class="stat">
              <div class="label">{html.escape(label)}</div>
              <div class="value">{value}</div>
            </div>
            """
            for label, value in summary["zone_counts"].items()
        ) + f"""
            <div class="stat">
              <div class="label">Total cruces ROI</div>
              <div class="value">{sum(summary["zone_counts"].values())}</div>
            </div>
        """
    elif summary["count_only_full_passage"]:
        stats_html = f"""
            <div class="stat"><div class="label">Cruces completos ROI</div><div class="value">{summary["total_roi_passers"]}</div></div>
        """
    else:
        stats_html = f"""
            <div class="stat"><div class="label">{html.escape(summary["positive_label"])}</div><div class="value">{summary["flow_positive"]}</div></div>
            <div class="stat"><div class="label">{html.escape(summary["negative_label"])}</div><div class="value">{summary["flow_negative"]}</div></div>
            <div class="stat"><div class="label">Entradas ROI</div><div class="value">{summary["roi_entries"]}</div></div>
            <div class="stat"><div class="label">Salidas ROI</div><div class="value">{summary["roi_exits"]}</div></div>
        """

    event_rows = "\n".join(
        f"<tr><td>{e['frame_index']}</td><td>{e['track_id']}</td><td>{html.escape(e['event_type'])}</td><td>{html.escape(e.get('flow_label') or '-')}</td></tr>"
        for e in summary["event_log"][-30:]
    ) or '<tr><td colspan="4">Sin eventos</td></tr>'

    extra_html = ""
    if summary.get("extra_analysis_requested") and summary.get("extra_analysis_target", "").strip():
        extra_html = f"""
        <section class="panel">
          <h2>Análisis adicional solicitado</h2>
          <p><strong>Pedido:</strong> {html.escape(summary["extra_analysis_target"])}</p>
          <p class="muted">El notebook deja este pedido registrado, pero hoy el pipeline cuenta personas. Para gorros u otros atributos hay que sumar otro modelo.</p>
        </section>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="utf-8" />
      <style>
        :root {{ --bg:#f4efe6; --panel:#fffaf3; --ink:#1f2937; --muted:#6b7280; --line:#eadfce; }}
        body {{ margin:0; font-family:Georgia,serif; color:var(--ink); background:var(--bg); }}
        .wrap {{ max-width:1100px; margin:0 auto; padding:28px 18px 42px; }}
        .hero, .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:22px; padding:20px; }}
        .hero {{ display:grid; grid-template-columns:1.1fr .9fr; gap:18px; margin-bottom:20px; }}
        .stats {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:14px; margin-bottom:20px; }}
        .stat {{ background:white; border:1px solid var(--line); border-radius:18px; padding:16px; }}
        .label {{ color:var(--muted); text-transform:uppercase; font-size:.85rem; }}
        .value {{ font-size:2rem; font-weight:700; margin-top:8px; }}
        table {{ width:100%; border-collapse:collapse; }}
        th, td {{ text-align:left; padding:10px; border-bottom:1px solid var(--line); }}
        .preview img {{ width:100%; border-radius:14px; }}
        .muted {{ color:var(--muted); }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <section class="hero">
          <div>
            <p class="muted">Procesado el {html.escape(summary["processed_at"])}</p>
            <h1>{html.escape(summary["video_title"])}</h1>
            <p>Video: <code>{html.escape(summary["source_path"])}</code></p>
            <p>Frames procesados: <strong>{summary["frames_processed"]}</strong> a <strong>{summary["fps"]:.2f} FPS</strong></p>
          </div>
          <div>{preview_html}</div>
        </section>
        <section class="stats">{stats_html}</section>
        <section class="panel">
          <h2>Últimos eventos</h2>
          <table>
            <thead><tr><th>Frame</th><th>Track</th><th>Evento</th><th>Flujo</th></tr></thead>
            <tbody>{event_rows}</tbody>
          </table>
        </section>
        {extra_html}
      </div>
    </body>
    </html>
    """


def notebook_create_db_schema(database_url: str):
    create_sql = """
    CREATE TABLE IF NOT EXISTS video_event_stats (
        id BIGSERIAL PRIMARY KEY,
        processed_at TIMESTAMPTZ NOT NULL,
        video_key TEXT NOT NULL,
        video_title TEXT NOT NULL,
        track_id BIGINT NOT NULL,
        event_type TEXT NOT NULL,
        flow_label TEXT,
        action_label TEXT,
        frame_index INTEGER NOT NULL,
        extra_analysis_requested BOOLEAN NOT NULL DEFAULT FALSE,
        extra_analysis_target TEXT
    );
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()


def notebook_rows_for_db(summary: dict) -> list[tuple]:
    rows = []
    for event in summary["event_log"]:
        flow_label = event.get("flow_label")
        event_type = event["event_type"]
        action_label = flow_label or event_type
        rows.append(
            (
                summary["processed_at"],
                summary["video_key"],
                summary["video_title"],
                int(event["track_id"]),
                event_type,
                flow_label,
                action_label,
                int(event["frame_index"]),
                bool(summary.get("extra_analysis_requested", False)),
                summary.get("extra_analysis_target", ""),
            )
        )
    return rows


def notebook_save_summary_to_db(summary: dict, database_url: str):
    notebook_create_db_schema(database_url)
    rows = notebook_rows_for_db(summary)
    if not rows:
        return 0
    insert_sql = """
    INSERT INTO video_event_stats (
        processed_at, video_key, video_title, track_id, event_type,
        flow_label, action_label, frame_index, extra_analysis_requested, extra_analysis_target
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)
        conn.commit()
    return len(rows)
'''
    ),
    code_cell(
        r'''
def notebook_process_video(video_key: str, write_video: bool = False, extra_analysis_requested: bool = False, extra_analysis_target: str = "") -> dict:
    config = NOTEBOOK_VIDEO_CONFIGS[video_key]
    if not Path(config.path).exists():
        raise FileNotFoundError(f"No se encontró el video: {config.path}")

    cap = cv2.VideoCapture(config.path)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir el video: {config.path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("/content/outputs")
    reports_dir = Path("/content/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_video_path = output_dir / f"{video_key}_{timestamp}.mp4"

    writer = None
    if write_video:
        writer = cv2.VideoWriter(str(output_video_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        if not writer.isOpened():
            raise RuntimeError("No se pudo abrir el VideoWriter.")

    model = YOLO("yolo11n.pt")
    engine = NotebookCounterEngine(config)
    frame_index = 0
    preview_frame = None

    try:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            results = model.track(frame, persist=True, verbose=False, classes=[0], conf=0.3, tracker="bytetrack.yaml")
            visible_tracks = []
            active_ids = set()
            result = results[0]
            if result.boxes is not None and result.boxes.id is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                ids = result.boxes.id.cpu().numpy().astype(int)
                for bbox, track_id in zip(boxes, ids):
                    bbox_tuple = tuple(map(float, bbox.tolist()))
                    tracking_point = notebook_tracking_point(config, bbox_tuple)
                    center = notebook_center_point(bbox_tuple)
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
            annotated = notebook_annotate_frame(frame, config, engine, visible_tracks)
            if preview_frame is None and visible_tracks:
                preview_frame = annotated.copy()
            if writer is not None:
                writer.write(annotated)
            frame_index += 1
    finally:
        cap.release()
        if writer is not None:
            writer.release()

    preview_path = reports_dir / f"{video_key}_{timestamp}_preview.jpg"
    if preview_frame is not None:
        cv2.imwrite(str(preview_path), preview_frame)
    else:
        preview_path = None

    summary = {
        "video_key": config.key,
        "video_title": config.title,
        "source_path": config.path,
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "frames_processed": frame_index,
        "fps": float(fps),
        "roi_entries": engine.roi_entries,
        "roi_exits": engine.roi_exits,
        "total_roi_passers": engine.total_roi_passers,
        "flow_positive": engine.flow_positive,
        "flow_negative": engine.flow_negative,
        "positive_label": config.positive_label,
        "negative_label": config.negative_label,
        "count_only_full_passage": config.count_only_full_passage,
        "zone_counts": engine.zone_counts,
        "extra_analysis_requested": extra_analysis_requested,
        "extra_analysis_target": extra_analysis_target.strip(),
        "output_video": str(output_video_path) if writer is not None else "",
        "preview_path": str(preview_path) if preview_path else "",
        "event_log": engine.events,
    }
    report_html = notebook_generate_report_html(summary)
    report_path = reports_dir / f"{video_key}_{timestamp}.html"
    report_path.write_text(report_html, encoding="utf-8")
    summary["report_path"] = str(report_path)
    return summary
'''
    ),
    code_cell(
        r'''
video_dropdown = widgets.Dropdown(
    options=[(cfg.title, key) for key, cfg in NOTEBOOK_VIDEO_CONFIGS.items()],
    value="mall",
    description="Video:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="500px"),
)

write_video_checkbox = widgets.Checkbox(value=False, description="Generar video anotado", indent=False)
extra_analysis_checkbox = widgets.Checkbox(value=False, description="Quiero analizar otra cosa además de personas", indent=False)
extra_analysis_text = widgets.Text(
    value="",
    placeholder="Ej: cuántos llevan gorro",
    description="Análisis extra:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="700px"),
)
save_db_checkbox = widgets.Checkbox(value=True, description="Guardar eventos en PostgreSQL", indent=False)
db_url_text = widgets.Text(
    value=DATABASE_URL_DEFAULT,
    description="PostgreSQL URL:",
    style={"description_width": "initial"},
    layout=widgets.Layout(width="100%"),
)
run_button = widgets.Button(description="Procesar video", button_style="success", icon="play")
ui_output = widgets.Output()


def run_notebook_processing(_):
    with ui_output:
        clear_output(wait=True)
        selected_key = video_dropdown.value
        print(f"Procesando: {NOTEBOOK_VIDEO_CONFIGS[selected_key].title}")
        try:
            summary = notebook_process_video(
                selected_key,
                write_video=write_video_checkbox.value,
                extra_analysis_requested=extra_analysis_checkbox.value,
                extra_analysis_target=extra_analysis_text.value,
            )
            display(HTML(notebook_generate_report_html(summary)))

            if save_db_checkbox.value:
                inserted_rows = notebook_save_summary_to_db(summary, db_url_text.value)
                print(f"Eventos guardados en PostgreSQL: {inserted_rows}")

            print(f"Reporte HTML: {summary['report_path']}")
            if summary["output_video"]:
                print(f"Video anotado: {summary['output_video']}")
                display(Video(summary["output_video"], embed=True))
        except Exception as exc:
            print(f"Error: {exc}")
            raise


run_button.on_click(run_notebook_processing)

display(
    widgets.VBox(
        [
            widgets.HTML("<h3>Panel de análisis para Colab</h3>"),
            video_dropdown,
            write_video_checkbox,
            extra_analysis_checkbox,
            extra_analysis_text,
            save_db_checkbox,
            db_url_text,
            run_button,
            ui_output,
        ]
    )
)
'''
    ),
]


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    filtered_cells = []
    for cell in notebook["cells"]:
        source = "".join(cell.get("source", []))
        if COLAB_MARKER in source:
            continue
        filtered_cells.append(cell)

    notebook["cells"] = filtered_cells + NEW_CELLS
    NOTEBOOK_PATH.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
