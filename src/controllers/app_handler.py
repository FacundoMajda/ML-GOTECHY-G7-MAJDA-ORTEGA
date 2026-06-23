# src/controllers/app_handler.py
import json
import mimetypes
import re
import shutil
import threading
import traceback
import uuid
from cgi import FieldStorage
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

from src.config.settings import REPORTS_DIR, UPLOADS_DIR
from src.models.contracts import ROIConfig, VideoSourceConfig
from src.models.enums import SourceType
from src.providers.youtube_utils import extract_stream_url
from src.repositories.occupancy_snapshot_repo import OccupancySnapshotRepository
from src.repositories.roi_repo import ROIRepository
from src.repositories.session_repo import SessionRepository
from src.repositories.video_source_repo import VideoSourceRepository
from src.repositories.zone_event_repo import ZoneEventRepository
from src.services.analytics_service import AnalyticsService
from src.services.metrics_service import MetricsService
from src.services.report_service import generate_report_html
from src.utils.html_utils import render_home


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_PATH = BASE_DIR / UPLOADS_DIR

_repo = VideoSourceRepository()
_session_repo = SessionRepository()
_roi_repo = ROIRepository()
_snapshot_repo = OccupancySnapshotRepository()
_zone_repo = ZoneEventRepository()

# ── Job progress (thread-safe) ─────────────────────────────────────────────
_job_progress: dict = {}
_job_lock: threading.Lock = threading.Lock()

# ── Frame dimensions cache ─────────────────────────────────────────────────
_frame_dim_cache: dict[str, tuple[int, int]] = {}
_frame_dim_lock: threading.Lock = threading.Lock()

# ── Tracking class name → YOLO class ID mapping ────────────────────────────
_TRACKING_CLASS_TO_YOLO = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "backpack": 24,
}


def _run_analysis(
    video_source_id: str,
    output_video: bool,
    tracking_classes: list[int] | None,
    frame_skip: int,
    max_seconds: int | None,
) -> None:
    """Run analysis in background thread, updating _job_progress."""
    print(f"[DEBUG] _run_analysis: ENTRY video_source_id={video_source_id} output_video={output_video} tracking_classes={tracking_classes} frame_skip={frame_skip} max_seconds={max_seconds}", flush=True)
    try:
        config = _repo.get_by_id(video_source_id)
        print(f"[DEBUG] _run_analysis: after _repo.get_by_id -> config={config}", flush=True)
        if config is None:
            raise ValueError(f"Video source not found: {video_source_id}")
        rois = _roi_repo.list_by_source(video_source_id)
        print(f"[DEBUG] _run_analysis: after _roi_repo.list_by_source -> {len(rois)} rois", flush=True)

        service = AnalyticsService(config, rois, persist=True)

        def _progress_callback(frames_done: int, total_frames: int | None, seconds_done: float, total_seconds: float | None) -> None:
            with _job_lock:
                _job_progress["frames_done"] = frames_done
                _job_progress["total_frames"] = total_frames
                _job_progress["seconds_done"] = seconds_done
                _job_progress["total_seconds"] = total_seconds
                if total_seconds and total_seconds > 0:
                    _job_progress["progress"] = min(seconds_done / total_seconds, 1.0)
                    _job_progress["message"] = f"Processing frames: {seconds_done:.1f}/{total_seconds:.1f}s ({frames_done} frames)"
                elif total_frames and total_frames > 0:
                    _job_progress["progress"] = frames_done / total_frames
                    _job_progress["message"] = f"Processing frames: {frames_done}/{total_frames}"
                else:
                    _job_progress["message"] = f"Processing frames: {seconds_done:.1f}s"

        print(f"[DEBUG] _run_analysis: calling service.process()...", flush=True)
        result = service.process(
            write_video=output_video,
            extra_analysis=None,
            tracking_classes=tracking_classes,
            frame_skip=frame_skip,
            max_seconds=max_seconds,
            progress_callback=_progress_callback,
        )
        print(f"[DEBUG] _run_analysis: after service.process() -> result.id={result.id}", flush=True)

        # Feedback post-procesamiento — UI ya no se queda congelada
        with _job_lock:
            _job_progress["message"] = "Saving results to database..."
            _job_progress["timestamp"] = datetime.now().isoformat()

        # Save report HTML to disk
        print(f"[DEBUG] _run_analysis: calling generate_report_html(str(result.id))", flush=True)
        report_html = generate_report_html(str(result.id))
        report_path = Path(REPORTS_DIR) / f"{result.id}.html"
        print(f"[DEBUG] _run_analysis: writing report to {report_path}", flush=True)
        report_path.write_text(report_html, encoding="utf-8")
        print(f"[DEBUG] _run_analysis: after report_path.write_text()", flush=True)

        with _job_lock:
            _job_progress["running"] = False
            _job_progress["session_id"] = result.id
            _job_progress["error"] = None
            _job_progress["timestamp"] = datetime.now().isoformat()
            _job_progress["message"] = "Analysis complete"
            print(f"[DEBUG] _run_analysis: _job_progress set -> {dict(_job_progress)}", flush=True)
    except Exception as exc:
        print(f"[DEBUG] _run_analysis: EXCEPTION {exc}", flush=True)
        traceback.print_exc()
        with _job_lock:
            _job_progress["running"] = False
            _job_progress["error"] = str(exc)
            _job_progress["timestamp"] = datetime.now().isoformat()
            _job_progress["message"] = "Analysis failed"
            print(f"[DEBUG] _run_analysis: _job_progress after exception -> {dict(_job_progress)}", flush=True)
    print(f"[DEBUG] _run_analysis: EXIT", flush=True)


def _get_frame_dimensions(source_id: str) -> tuple[int, int]:
    """Lazy-cache frame dimensions for a video source."""
    print(f"[DEBUG] _get_frame_dimensions: ENTRY source_id={source_id}", flush=True)
    with _frame_dim_lock:
        if source_id in _frame_dim_cache:
            cached = _frame_dim_cache[source_id]
            print(f"[DEBUG] _get_frame_dimensions: returning from cache -> {cached}", flush=True)
            return cached

    config = _repo.get_by_id(source_id)
    if config is None:
        print(f"[DEBUG] _get_frame_dimensions: config is None, returning (0,0)", flush=True)
        return (0, 0)

    try:
        uri = config.source_uri
        if config.source_type in (SourceType.YOUTUBE_VOD, SourceType.YOUTUBE_LIVE):
            uri = extract_stream_url(uri)

        print(f"[DEBUG] _get_frame_dimensions: opening VideoCapture uri={uri[:80]}...", flush=True)
        cap = cv2.VideoCapture(uri, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(f"[DEBUG] _get_frame_dimensions: VideoCapture not opened, returning (0,0)", flush=True)
            return (0, 0)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            print(f"[DEBUG] _get_frame_dimensions: frame read failed, returning (0,0)", flush=True)
            return (0, 0)
        h, w = frame.shape[:2]
        with _frame_dim_lock:
            _frame_dim_cache[source_id] = (w, h)
        print(f"[DEBUG] _get_frame_dimensions: returning ({w}, {h})", flush=True)
        return (w, h)
    except Exception:
        print(f"[DEBUG] _get_frame_dimensions: exception caught, returning (0,0)", flush=True)
        return (0, 0)


def _load_video_sources() -> list[tuple[VideoSourceConfig, list[ROIConfig]]]:
    print(f"[DEBUG] _load_video_sources: ENTRY", flush=True)
    try:
        sources = _repo.list_all()
        result = [(src, _roi_repo.list_by_source(src.id)) for src in sources]
        print(f"[DEBUG] _load_video_sources: got {len(result)} sources, returning", flush=True)
        return result
    except Exception as exc:
        print(f"[DEBUG] _load_video_sources: exception {exc}", flush=True)
        traceback.print_exc()
        return []


def _source_to_dict(src: VideoSourceConfig, rois: list[ROIConfig]) -> dict:
    print(f"[DEBUG] _source_to_dict: ENTRY src.id={src.id} rois={len(rois)}", flush=True)
    fw, fh = _get_frame_dimensions(src.id)
    result = {
        "id": src.id,
        "name": src.name,
        "source_type": src.source_type.value,
        "source_uri": src.source_uri,
        "is_live": src.is_live,
        "frame_width": fw,
        "frame_height": fh,
        "rois": [
            {
                "id": r.id,
                "name": r.name,
                "polygon": r.polygon,
                "positive_label": r.positive_label,
                "negative_label": r.negative_label,
                "detect_entry": r.detect_entry,
                "detect_exit": r.detect_exit,
                "detect_occupancy": r.detect_occupancy,
                "detect_dwell": r.detect_dwell,
                "alerts": r.alerts,
            }
            for r in rois
        ],
    }
    print(f"[DEBUG] _source_to_dict: returning id={src.id} frame_width={fw} frame_height={fh}", flush=True)
    return result


# ── Route tables ──────────────────────────────────────────────────────────────

ROUTES_GET = {
    "/api/sources": "_api_sources",
    re.compile(r"^/api/sources/([^/]+)/preview$"): "_api_source_preview",
    "/api/sessions": "_api_session_list",
    re.compile(r"^/api/sessions/([^/]+)/report$"): "_api_session_report",
    "/api/analytics/occupancy-trends": "_api_occupancy_trends",
    "/api/analytics/dwell-times": "_api_dwell_times",
    "/api/job/status": "_api_job_status",
    # New clean endpoints
    "/api/dashboard": "_api_dashboard",
    "/api/analyses": "_api_analyses_list",
    re.compile(r"^/api/analyses/([^/]+)$"): "_api_analyses_detail",
}

ROUTES_POST = {
    "/api/uploads": "_handle_upload_file",
    "/api/sources": "_handle_create_source",
    re.compile(r"^/api/sources/([^/]+)/rois$"): "_api_create_roi",
    "/process": "_handle_process",
}

ROUTES_DELETE = {
    re.compile(r"^/api/rois/([^/]+)$"): "_api_delete_roi",
    re.compile(r"^/api/sources/([^/]+)$"): "_api_delete_source",
}

ROUTES_PUT = {
    re.compile(r"^/api/rois/([^/]+)/config$"): "_api_update_roi_config",
}


class AppHandler(BaseHTTPRequestHandler):
    # ── Router ──────────────────────────────────────────────────────────────

    def _route(self, method: str, path: str) -> None:
        route_table = {"GET": ROUTES_GET, "POST": ROUTES_POST, "DELETE": ROUTES_DELETE, "PUT": ROUTES_PUT}
        routes = route_table.get(method, {})
        # Literal match first
        handler_name = routes.get(path)
        if handler_name:
            getattr(self, handler_name)()
            return
        # Regex match
        for pattern, handler_name in routes.items():
            if isinstance(pattern, re.Pattern):
                m = pattern.match(path)
                if m:
                    getattr(self, handler_name)(*m.groups())
                    return
        self.send_error(404)

    # ── HTTP method handlers ───────────────────────────────────────────────

    def do_GET(self) -> None:
        print(f"[DEBUG] AppHandler.do_GET: path={self.path}", flush=True)
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_html(render_home())
            return

        if path.startswith("/files/"):
            rel = path.removeprefix("/files/")
            file_path = (BASE_DIR / rel).resolve()
            if not str(file_path).startswith(str(BASE_DIR)):
                self.send_error(403)
                return
            if not file_path.exists() or not file_path.is_file():
                self.send_error(404)
                return
            self._send_file(file_path)
            return

        self._route("GET", path)

    def do_POST(self) -> None:
        print(f"[DEBUG] AppHandler.do_POST: path={self.path}", flush=True)
        parsed = urlparse(self.path)
        self._route("POST", parsed.path)

    def do_DELETE(self) -> None:
        print(f"[DEBUG] AppHandler.do_DELETE: path={self.path}", flush=True)
        parsed = urlparse(self.path)
        self._route("DELETE", parsed.path)

    def do_PUT(self) -> None:
        print(f"[DEBUG] AppHandler.do_PUT: path={self.path}", flush=True)
        parsed = urlparse(self.path)
        self._route("PUT", parsed.path)

    # ── API handlers — GET ────────────────────────────────────────────────

    def _api_sources(self) -> None:
        """GET /api/sources"""
        print(f"[DEBUG] AppHandler._api_sources: ENTRY", flush=True)
        sources = _load_video_sources()
        data = [_source_to_dict(s, r) for s, r in sources]
        print(f"[DEBUG] AppHandler._api_sources: returning {len(data)} sources", flush=True)
        self._send_json(200, data)

    def _api_source_preview(self, source_id: str) -> None:
        """GET /api/sources/<id>/preview — primer frame con ROIs dibujados como JPEG"""
        print(f"[DEBUG] AppHandler._api_source_preview: ENTRY source_id={source_id}", flush=True)
        config = _repo.get_by_id(source_id)
        if config is None:
            print(f"[DEBUG] AppHandler._api_source_preview: config not found, 404", flush=True)
            self._send_json(404, {"error": "Source not found"})
            return

        try:
            # Resolve URI: for YouTube, get actual stream URL via yt-dlp
            uri = config.source_uri
            if config.source_type in (SourceType.YOUTUBE_VOD, SourceType.YOUTUBE_LIVE):
                uri = extract_stream_url(uri)

            cap = cv2.VideoCapture(uri, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                print(f"[DEBUG] AppHandler._api_source_preview: VideoCapture not opened, 404", flush=True)
                self._send_json(404, {"error": "Cannot open video source"})
                return
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                print(f"[DEBUG] AppHandler._api_source_preview: frame read failed, 404", flush=True)
                self._send_json(404, {"error": "Cannot read frame"})
                return

            # Resize para preview (max 640px de ancho)
            h, w = frame.shape[:2]
            scale = 1.0
            if w > 640:
                scale = 640 / w
                new_w, new_h = int(w * scale), int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))

            # ── Dibujar ROIs ──
            rois = _roi_repo.list_by_source(source_id)
            overlay = frame.copy()
            for roi in rois:
                pts = np.array(roi.polygon, dtype=np.int32)
                if w > 640:
                    pts = (pts * scale).astype(np.int32)
                cv2.polylines(overlay, [pts], isClosed=True, color=(15, 118, 110), thickness=2)
                # Fill with semi-transparent color
                cv2.fillPoly(overlay, [pts], color=(15, 118, 110, 60))
                # Label
                cx = int(pts[:, 0].mean())
                cy = int(pts[:, 1].mean())
                cv2.putText(overlay, roi.name, (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(overlay, roi.name, (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (15, 118, 110), 1, cv2.LINE_AA)

            # Blend overlay with original
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                print(f"[DEBUG] AppHandler._api_source_preview: JPEG encode failed, 500", flush=True)
                self._send_json(500, {"error": "JPEG encode failed"})
                return

            print(f"[DEBUG] AppHandler._api_source_preview: sending JPEG ({len(buf)} bytes)", flush=True)
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf.tobytes())
        except Exception as e:
            print(f"[DEBUG] AppHandler._api_source_preview: EXCEPTION {e}", flush=True)
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def _api_session_list(self) -> None:
        """GET /api/sessions"""
        print(f"[DEBUG] AppHandler._api_session_list: ENTRY", flush=True)
        sessions = _session_repo.list_all()
        print(f"[DEBUG] AppHandler._api_session_list: returning {len(sessions)} sessions", flush=True)
        self._send_json(200, sessions)

    def _api_session_report(self, session_id: str) -> None:
        """GET /api/sessions/<id>/report"""
        print(f"[DEBUG] AppHandler._api_session_report: ENTRY session_id={session_id}", flush=True)
        path = Path(REPORTS_DIR) / f"{session_id}.html"
        if not path.exists():
            print(f"[DEBUG] AppHandler._api_session_report: report not found at {path}, 404", flush=True)
            self._send_json(404, {"error": "Report not found"})
            return
        print(f"[DEBUG] AppHandler._api_session_report: sending report ({path.stat().st_size} bytes)", flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _api_occupancy_trends(self) -> None:
        """GET /api/analytics/occupancy-trends"""
        print(f"[DEBUG] AppHandler._api_occupancy_trends: ENTRY", flush=True)
        try:
            data = _snapshot_repo.get_occupancy_trends()
            self._send_json(200, data)
        except Exception as e:
            print(f"[DEBUG] AppHandler._api_occupancy_trends: EXCEPTION {e}", flush=True)
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def _api_dwell_times(self) -> None:
        """GET /api/analytics/dwell-times"""
        print(f"[DEBUG] AppHandler._api_dwell_times: ENTRY", flush=True)
        try:
            data = _zone_repo.get_dwell_times()
            self._send_json(200, data)
        except Exception as e:
            print(f"[DEBUG] AppHandler._api_dwell_times: EXCEPTION {e}", flush=True)
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def _api_job_status(self) -> None:
        """GET /api/job/status"""
        print(f"[DEBUG] AppHandler._api_job_status: ENTRY", flush=True)
        with _job_lock:
            status = dict(_job_progress)

        if not status:
            status = {
                "running": False,
                "progress": 0.0,
                "frames_done": 0,
                "total_frames": None,
                "seconds_done": 0.0,
                "total_seconds": None,
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "message": "No job running",
            }

        # Ensure all expected keys are present
        status.setdefault("running", False)
        status.setdefault("progress", 0.0)
        status.setdefault("frames_done", 0)
        status.setdefault("total_frames", None)
        status.setdefault("seconds_done", 0.0)
        status.setdefault("total_seconds", None)
        status.setdefault("error", None)
        status.setdefault("timestamp", datetime.now().isoformat())
        status.setdefault("message", "")

        print(f"[DEBUG] AppHandler._api_job_status: full status dict -> {status}", flush=True)
        self._send_json(200, status)


    # -- New clean API - Dashboard / Analyses ---

    def _api_dashboard(self) -> None:
        print('[DEBUG] AppHandler._api_dashboard: ENTRY', flush=True)
        try:
            data = MetricsService().get_dashboard()
            self._send_json(200, data)
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {'error': str(e)})

    def _api_analyses_list(self) -> None:
        print('[DEBUG] AppHandler._api_analyses_list: ENTRY', flush=True)
        try:
            sessions = _session_repo.list_all()
            cleaned = [
                {
                    'id': s['id'],
                    'source_name': s.get('source_name'),
                    'source_type': s.get('source_type'),
                    'started_at': s.get('started_at'),
                    'ended_at': s.get('ended_at'),
                    'duration_seconds': s.get('duration_seconds'),
                    'status': s.get('status', 'completed'),
                }
                for s in sessions
            ]
            self._send_json(200, cleaned)
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {'error': str(e)})

    def _api_analyses_detail(self, session_id: str) -> None:
        print('[DEBUG] AppHandler._api_analyses_detail: ENTRY session_id=' + session_id, flush=True)
        try:
            session = _session_repo.get_by_id(session_id)
            if not session:
                self._send_json(404, {'error': 'Analysis not found'})
                return
            from src.repositories.metric_snapshot_repo import MetricSnapshotRepository
            snaps = MetricSnapshotRepository().get_by_session(uuid.UUID(session_id))
            cleaned_snaps = [
                {
                    'roi_id': str(s['roi_id']),
                    'entries': s['entries'],
                    'exits': s['exits'],
                    'max_occupancy': s['max_occupancy'],
                    'avg_dwell_seconds': s['avg_dwell_seconds'],
                    'computed_at': str(s['computed_at']) if s.get('computed_at') else None,
                }
                for s in snaps
            ]
            self._send_json(200, {
                'id': session['id'],
                'source_name': session.get('source_name'),
                'source_type': session.get('source_type'),
                'started_at': session.get('started_at'),
                'ended_at': session.get('ended_at'),
                'duration_seconds': session.get('duration_seconds'),
                'status': session.get('status', 'completed'),
                'metrics': cleaned_snaps,
            })
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {'error': str(e)})

    # ── API handlers — POST ───────────────────────────────────────────────

    def _handle_upload_file(self) -> None:
        """POST /api/uploads - multipart/form-data with field 'file'."""
        print(f"[DEBUG] AppHandler._handle_upload_file: ENTRY", flush=True)
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            print(f"[DEBUG] AppHandler._handle_upload_file: content-type not multipart, 400", flush=True)
            self._send_json(400, {"error": "multipart/form-data is required"})
            return

        form = FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": ctype,
            },
        )

        file_item = form["file"] if "file" in form else None
        if file_item is None or not getattr(file_item, "file", None):
            print(f"[DEBUG] AppHandler._handle_upload_file: no file field, 400", flush=True)
            self._send_json(400, {"error": "file field is required"})
            return

        original_name = Path(file_item.filename or "upload.mp4").name
        if not original_name:
            original_name = "upload.mp4"

        ext = Path(original_name).suffix or ".mp4"
        safe_stem = Path(original_name).stem.strip().replace(" ", "_") or "upload"
        filename = f"{safe_stem}_{uuid.uuid4().hex[:8]}{ext}"

        UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
        target = UPLOADS_PATH / filename

        with target.open("wb") as fh:
            shutil.copyfileobj(file_item.file, fh)

        print(f"[DEBUG] AppHandler._handle_upload_file: saved file -> {filename}", flush=True)
        self._send_json(
            201,
            {
                "filename": filename,
                "original_name": original_name,
                "path": str(target),
                "relative_path": str(target.relative_to(BASE_DIR)).replace("\\", "/"),
            },
        )

    def _handle_create_source(self) -> None:
        """POST /api/sources"""
        print(f"[DEBUG] AppHandler._handle_create_source: ENTRY", flush=True)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        name = body.get("name", "").strip()
        source_type = body.get("source_type", "").strip()
        source_uri = body.get("source_uri", "").strip()

        valid_types = ("file", "youtube_vod", "youtube_live", "rtsp")
        errors = []
        if not name:
            errors.append("name is required")
        if source_type not in valid_types:
            errors.append(f"source_type must be one of {valid_types}")
        if not source_uri:
            errors.append("source_uri is required")
        elif source_type == SourceType.FILE.value and not Path(source_uri).exists():
            errors.append("uploaded file was not found on disk")

        if errors:
            print(f"[DEBUG] AppHandler._handle_create_source: validation errors -> {errors}", flush=True)
            self._send_json(400, {"error": "; ".join(errors)})
            return

        try:
            source_id = str(uuid.uuid4())
            source_type_enum = SourceType(source_type)
            is_live = source_type_enum in (SourceType.YOUTUBE_LIVE, SourceType.RTSP)

            config = VideoSourceConfig(
                id=source_id,
                name=name,
                source_type=source_type_enum,
                source_uri=source_uri,
                is_live=is_live,
            )
            _repo.create(config)

            print(f"[DEBUG] AppHandler._handle_create_source: created source {source_id}", flush=True)
            self._send_json(201, {
                "id": source_id,
                "name": name,
                "source_type": source_type,
                "source_uri": source_uri,
                "is_live": is_live,
                "rois": [],
            })
        except Exception as e:
            print(f"[DEBUG] AppHandler._handle_create_source: EXCEPTION {e}", flush=True)
            traceback.print_exc()
            self._send_json(400, {"error": str(e)})

    def _handle_process(self) -> None:
        print(f"[DEBUG] AppHandler._handle_process: ENTRY", flush=True)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            body = json.loads(raw) if raw else {}
            video_source_id = body.get("video_source_id", "")
            output = body.get("output", {})
            output_video = output.get("annotated_video", True)

            # New fields
            tracking_classes_raw = body.get("tracking_classes")
            if tracking_classes_raw and isinstance(tracking_classes_raw, list):
                tracking_class_ids = [
                    _TRACKING_CLASS_TO_YOLO.get(cls, 0) for cls in tracking_classes_raw
                ]
            else:
                tracking_class_ids = None  # default: person only (backward compat)
            frame_skip = body.get("frame_skip", 1)
            try:
                frame_skip = int(frame_skip)
            except (ValueError, TypeError):
                frame_skip = 1
            if frame_skip < 1:
                frame_skip = 1

            max_seconds = body.get("max_seconds")
            if max_seconds is None:
                max_frames = body.get("max_frames")
                if max_frames is not None:
                    try:
                        max_frames = int(max_frames)
                    except (ValueError, TypeError):
                        max_frames = None
                    max_seconds = max_frames
            if max_seconds is not None:
                try:
                    max_seconds = int(max_seconds)
                except (ValueError, TypeError):
                    max_seconds = None
            if max_seconds is not None and max_seconds <= 0:
                max_seconds = None
        else:
            # Backward compat: form-urlencoded (no new fields)
            form = parse_qs(raw.decode("utf-8"))
            video_source_id = form.get("video_source_id", [""])[0]
            output_video = form.get("output_video", [""])[0] == "on"
            tracking_class_ids = None
            frame_skip = 1
            max_seconds = None

        print(f"[DEBUG] AppHandler._handle_process: video_source_id={video_source_id} output_video={output_video} tracking_class_ids={tracking_class_ids} frame_skip={frame_skip} max_seconds={max_seconds}", flush=True)

        # Validate source exists before spawning thread
        config = _repo.get_by_id(video_source_id)
        if config is None:
            print(f"[DEBUG] AppHandler._handle_process: source not found, 404", flush=True)
            self._send_json(404, {"error": f"Video source not found: {video_source_id}"})
            return

        # Set job progress and spawn background thread
        with _job_lock:
            _job_progress.clear()
            _job_progress.update({
                "running": True,
                "progress": 0.0,
                "frames_done": 0,
                "total_frames": None,
                "seconds_done": 0.0,
                "total_seconds": max_seconds,
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "message": "Starting analysis...",
            })
            print(f"[DEBUG] AppHandler._handle_process: _job_progress initialized -> {dict(_job_progress)}", flush=True)

        thread = threading.Thread(
            target=_run_analysis,
            args=(video_source_id, output_video, tracking_class_ids, frame_skip, max_seconds),
            daemon=True,
        )
        thread.start()

        self._send_json(200, {"status": "started"})

    def _api_create_roi(self, source_id: str) -> None:
        """POST /api/sources/<id>/rois"""
        print(f"[DEBUG] AppHandler._api_create_roi: ENTRY source_id={source_id}", flush=True)
        # Validate source exists
        config = _repo.get_by_id(source_id)
        if config is None:
            print(f"[DEBUG] AppHandler._api_create_roi: source not found, 404", flush=True)
            self._send_json(404, {"error": "Source not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        name = body.get("name", "").strip()
        polygon = body.get("polygon")

        if not name:
            print(f"[DEBUG] AppHandler._api_create_roi: name required, 400", flush=True)
            self._send_json(400, {"error": "name is required"})
            return

        if not polygon or not isinstance(polygon, list) or len(polygon) < 3:
            print(f"[DEBUG] AppHandler._api_create_roi: invalid polygon, 400", flush=True)
            self._send_json(400, {"error": "polygon must have at least 3 points"})
            return

        for point in polygon:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                print(f"[DEBUG] AppHandler._api_create_roi: invalid point, 400", flush=True)
                self._send_json(400, {"error": "each polygon point must be [x, y]"})
                return

        roi_id = str(uuid.uuid4())
        roi = ROIConfig(id=roi_id, name=name, polygon=polygon)
        _roi_repo.create(roi, source_id)

        print(f"[DEBUG] AppHandler._api_create_roi: created roi {roi_id}", flush=True)
        self._send_json(201, {
            "id": roi.id,
            "name": roi.name,
            "polygon": roi.polygon,
            "positive_label": roi.positive_label,
            "negative_label": roi.negative_label,
            "detect_entry": roi.detect_entry,
            "detect_exit": roi.detect_exit,
            "detect_occupancy": roi.detect_occupancy,
            "detect_dwell": roi.detect_dwell,
            "alerts": roi.alerts,
        })

    # ── API handlers — DELETE ─────────────────────────────────────────────

    def _api_delete_roi(self, roi_id: str) -> None:
        """DELETE /api/rois/<id>"""
        print(f"[DEBUG] AppHandler._api_delete_roi: ENTRY roi_id={roi_id}", flush=True)
        existing = _roi_repo.get_by_id(roi_id)
        if existing is None:
            print(f"[DEBUG] AppHandler._api_delete_roi: roi not found, 404", flush=True)
            self._send_json(404, {"error": "ROI not found"})
            return

        _roi_repo.delete(roi_id)
        print(f"[DEBUG] AppHandler._api_delete_roi: deleted roi {roi_id}, 204", flush=True)
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _api_delete_source(self, source_id: str) -> None:
        """DELETE /api/sources/<id>"""
        print(f"[DEBUG] AppHandler._api_delete_source: ENTRY source_id={source_id}", flush=True)
        existing = _repo.get_by_id(source_id)
        if existing is None:
            print(f"[DEBUG] AppHandler._api_delete_source: source not found, 404", flush=True)
            self._send_json(404, {"error": "Source not found"})
            return

        _repo.delete(source_id)
        print(f"[DEBUG] AppHandler._api_delete_source: deleted source {source_id}, 204", flush=True)
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ── API handlers — PUT ────────────────────────────────────────────────

    def _api_update_roi_config(self, roi_id: str) -> None:
        """PUT /api/rois/<id>/config"""
        print(f"[DEBUG] AppHandler._api_update_roi_config: ENTRY roi_id={roi_id}", flush=True)
        existing = _roi_repo.get_by_id(roi_id)
        if existing is None:
            print(f"[DEBUG] AppHandler._api_update_roi_config: roi not found, 404", flush=True)
            self._send_json(404, {"error": "ROI not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        print(f"[DEBUG] AppHandler._api_update_roi_config: body={body}", flush=True)

        _roi_repo.update_config(roi_id, body)

        # Return updated fields
        updated = _roi_repo.get_by_id(roi_id)
        print(f"[DEBUG] AppHandler._api_update_roi_config: returning updated={updated}", flush=True)
        self._send_json(200, updated)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _send_json(self, status: int, data) -> None:
        print(f"[DEBUG] AppHandler._send_json: status={status} data_preview={str(data)[:200]}", flush=True)
        body = json.dumps(data).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            print(f"[DEBUG] AppHandler._send_json: sent {len(body)} bytes", flush=True)
        except (ConnectionAbortedError, BrokenPipeError) as e:
            print(f"[DEBUG] AppHandler._send_json: client disconnected: {e}", flush=True)
            pass  # cliente desconectado, no podemos hacer nada

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, payload: str, status: int = 200) -> None:
        print(f"[DEBUG] AppHandler._send_html: ENTRY status={status}", flush=True)
        content = payload.encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            print(f"[DEBUG] AppHandler._send_html: sent {len(content)} bytes", flush=True)
        except (ConnectionAbortedError, BrokenPipeError) as e:
            print(f"[DEBUG] AppHandler._send_html: client disconnected: {e}", flush=True)
            pass  # cliente desconectado, no podemos hacer nada

    def _send_file(self, file_path: Path) -> None:
        mime, _ = mimetypes.guess_type(str(file_path))
        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")
        print(f"[DEBUG] AppHandler._send_file: path={file_path} size={file_size} range={range_header}", flush=True)

        if range_header and range_header.startswith("bytes="):
            try:
                start_str, end_str = range_header.removeprefix("bytes=").split("-", 1)
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                start = max(0, min(start, file_size - 1))
                end = max(start, min(end, file_size - 1))
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.end_headers()

                with file_path.open("rb") as fh:
                    fh.seek(start)
                    self.wfile.write(fh.read(length))
                return
            except Exception as exc:
                print(f"[DEBUG] AppHandler._send_file: invalid range header -> {exc}", flush=True)

        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(file_size))
        self.end_headers()
        with file_path.open("rb") as fh:
            shutil.copyfileobj(fh, self.wfile)

