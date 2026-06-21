# src/controllers/app_handler.py
import json
import threading
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

from src.config.settings import REPORTS_DIR
from src.models.contracts import ROIConfig, VideoSourceConfig
from src.models.enums import SourceType
from src.repositories.session_repo import SessionRepository
from src.repositories.video_source_repo import VideoSourceRepository
from src.services.analytics_service import AnalyticsService
from src.services.report_service import generate_report_html
from src.utils.html_utils import render_home


BASE_DIR = Path(__file__).resolve().parent.parent

_repo = VideoSourceRepository()
_session_repo = SessionRepository()

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
    max_frames: int | None,
) -> None:
    """Run analysis in background thread, updating _job_progress."""
    try:
        config = _repo.get_by_id(video_source_id)
        if config is None:
            raise ValueError(f"Video source not found: {video_source_id}")
        rois = _repo.get_rois_for_source(video_source_id)

        service = AnalyticsService(config, rois, persist=True)

        def _progress_callback(frames_done: int, total_frames: int) -> None:
            with _job_lock:
                _job_progress["frames_done"] = frames_done
                _job_progress["total_frames"] = total_frames
                if total_frames and total_frames > 0:
                    _job_progress["progress"] = frames_done / total_frames
                _job_progress["message"] = f"Processed {frames_done}/{total_frames} frames"

        result = service.process(
            write_video=output_video,
            extra_analysis=None,
            tracking_classes=tracking_classes,
            frame_skip=frame_skip,
            max_frames=max_frames,
            progress_callback=_progress_callback,
        )

        # Save report HTML to disk
        report_html = generate_report_html(result)
        report_path = Path(REPORTS_DIR) / f"{result.id}.html"
        report_path.write_text(report_html, encoding="utf-8")

        with _job_lock:
            _job_progress["running"] = False
            _job_progress["session_id"] = result.id
            _job_progress["error"] = None
            _job_progress["timestamp"] = datetime.now().isoformat()
            _job_progress["message"] = "Analysis complete"
    except Exception as exc:
        with _job_lock:
            _job_progress["running"] = False
            _job_progress["error"] = str(exc)
            _job_progress["timestamp"] = datetime.now().isoformat()
            _job_progress["message"] = "Analysis failed"


def _get_frame_dimensions(source_id: str) -> tuple[int, int]:
    """Lazy-cache frame dimensions for a video source."""
    with _frame_dim_lock:
        if source_id in _frame_dim_cache:
            return _frame_dim_cache[source_id]

    config = _repo.get_by_id(source_id)
    if config is None:
        return (0, 0)

    try:
        uri = config.source_uri
        if config.source_type in (SourceType.YOUTUBE_VOD, SourceType.YOUTUBE_LIVE):
            import yt_dlp
            ydl_opts = {"quiet": True, "no_warnings": True, "format": "best[height<=480]"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(uri, download=False)
                uri = info.get("url") or uri

        cap = cv2.VideoCapture(uri, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            return (0, 0)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            return (0, 0)
        h, w = frame.shape[:2]
        with _frame_dim_lock:
            _frame_dim_cache[source_id] = (w, h)
        return (w, h)
    except Exception:
        return (0, 0)


def _load_video_sources() -> list[tuple[VideoSourceConfig, list[ROIConfig]]]:
    try:
        return _repo.get_all_with_rois()
    except Exception:
        return []


def _source_to_dict(src: VideoSourceConfig, rois: list[ROIConfig]) -> dict:
    fw, fh = _get_frame_dimensions(src.id)
    return {
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


class AppHandler(BaseHTTPRequestHandler):
    # ── API ──────────────────────────────────────────────────────────────────

    def _api_sources(self) -> None:
        """GET /api/sources"""
        sources = _load_video_sources()
        data = [_source_to_dict(s, r) for s, r in sources]
        self._send_json(200, data)

    def _api_source_preview(self, source_id: str) -> None:
        """GET /api/sources/<id>/preview — primer frame con ROIs dibujados como JPEG"""
        config = _repo.get_by_id(source_id)
        if config is None:
            self._send_json(404, {"error": "Source not found"})
            return

        try:
            # Resolve URI: for YouTube, get actual stream URL via yt-dlp
            uri = config.source_uri
            if config.source_type in (SourceType.YOUTUBE_VOD, SourceType.YOUTUBE_LIVE):
                import yt_dlp
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "format": "best[height<=480][ext=mp4]/best[height<=480]",
                    "youtube_include_dash_manifest": False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(uri, download=False)
                    uri = info.get("url") or uri

            cap = cv2.VideoCapture(uri, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                self._send_json(404, {"error": "Cannot open video source"})
                return
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                self._send_json(404, {"error": "Cannot read frame"})
                return

            # Resize para preview (max 640px de ancho)
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                new_w, new_h = int(w * scale), int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))

            # ── Dibujar ROIs ──
            rois = _repo.get_rois_for_source(source_id)
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
                self._send_json(500, {"error": "JPEG encode failed"})
                return

            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf.tobytes())
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _handle_create_source(self) -> None:
        """POST /api/sources"""
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

        if errors:
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

            self._send_json(201, {
                "id": source_id,
                "name": name,
                "source_type": source_type,
                "source_uri": source_uri,
                "is_live": is_live,
                "rois": [],
            })
        except Exception as e:
            self._send_json(400, {"error": str(e)})

    def _send_json(self, status: int, data) -> None:
        body = json.dumps(data).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError):
            pass  # cliente desconectado, no podemos hacer nada

    # ── HTTP ────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # API — sources
        if path == "/api/sources":
            self._api_sources()
            return

        if path.startswith("/api/sources/"):
            parts = path.removeprefix("/api/sources/").split("/", 1)
            source_id = parts[0]
            if len(parts) == 2 and parts[1] == "preview":
                self._api_source_preview(source_id)
                return
            self.send_error(404)
            return

        # API — sessions
        if path == "/api/sessions":
            self._api_session_list()
            return

        if path.startswith("/api/sessions/"):
            parts = path.removeprefix("/api/sessions/").split("/", 1)
            session_id = parts[0]
            if len(parts) == 2 and parts[1] == "report":
                self._api_session_report(session_id)
                return
            self.send_error(404)
            return

        # API — job status
        if path == "/api/job/status":
            self._api_job_status()
            return

        # Pages
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
            import mimetypes
            mime, _ = mimetypes.guess_type(str(file_path))
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
            return

        self.send_error(404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/rois/"):
            roi_id = path.removeprefix("/api/rois/")
            self._api_delete_roi(roi_id)
            return

        self.send_error(404)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/rois/") and path.endswith("/config"):
            roi_id = path.removeprefix("/api/rois/").removesuffix("/config")
            self._api_update_roi_config(roi_id)
            return

        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/sources":
            self._handle_create_source()
        elif path == "/process":
            self._handle_process()
        elif path.startswith("/api/sources/"):
            parts = path.removeprefix("/api/sources/").split("/", 1)
            if len(parts) == 2 and parts[1] == "rois":
                self._api_create_roi(parts[0])
                return
            self.send_error(404)
        else:
            self.send_error(404)

    def _handle_process(self) -> None:
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

            max_frames = body.get("max_frames")
            if max_frames is not None:
                try:
                    max_frames = int(max_frames)
                except (ValueError, TypeError):
                    max_frames = None
        else:
            # Backward compat: form-urlencoded (no new fields)
            form = parse_qs(raw.decode("utf-8"))
            video_source_id = form.get("video_source_id", [""])[0]
            output_video = form.get("output_video", [""])[0] == "on"
            tracking_class_ids = None
            frame_skip = 1
            max_frames = None

        # Validate source exists before spawning thread
        config = _repo.get_by_id(video_source_id)
        if config is None:
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
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "message": "Starting analysis...",
            })

        thread = threading.Thread(
            target=_run_analysis,
            args=(video_source_id, output_video, tracking_class_ids, frame_skip, max_frames),
            daemon=True,
        )
        thread.start()

        self._send_json(200, {"status": "started"})

    def _api_session_list(self) -> None:
        """GET /api/sessions"""
        sessions = _session_repo.list_all()
        self._send_json(200, sessions)

    def _api_session_report(self, session_id: str) -> None:
        """GET /api/sessions/<id>/report"""
        path = Path(REPORTS_DIR) / f"{session_id}.html"
        if not path.exists():
            self._send_json(404, {"error": "Report not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        self.wfile.write(path.read_bytes())

    # ── New API endpoints ────────────────────────────────────────────────────

    def _api_create_roi(self, source_id: str) -> None:
        """POST /api/sources/<id>/rois"""
        # Validate source exists
        config = _repo.get_by_id(source_id)
        if config is None:
            self._send_json(404, {"error": "Source not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        name = body.get("name", "").strip()
        polygon = body.get("polygon")

        if not name:
            self._send_json(400, {"error": "name is required"})
            return

        if not polygon or not isinstance(polygon, list) or len(polygon) < 3:
            self._send_json(400, {"error": "polygon must have at least 3 points"})
            return

        for point in polygon:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                self._send_json(400, {"error": "each polygon point must be [x, y]"})
                return

        roi_id = str(uuid.uuid4())
        roi = ROIConfig(id=roi_id, name=name, polygon=polygon)
        _repo.create_roi(roi, source_id)

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

    def _api_delete_roi(self, roi_id: str) -> None:
        """DELETE /api/rois/<id>"""
        existing = _repo.get_roi_by_id(roi_id)
        if existing is None:
            self._send_json(404, {"error": "ROI not found"})
            return

        _repo.delete_roi(roi_id)
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _api_update_roi_config(self, roi_id: str) -> None:
        """PUT /api/rois/<id>/config"""
        existing = _repo.get_roi_by_id(roi_id)
        if existing is None:
            self._send_json(404, {"error": "ROI not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        _repo.update_roi_config(roi_id, body)

        # Return updated fields
        updated = _repo.get_roi_by_id(roi_id)
        self._send_json(200, updated)

    def _api_job_status(self) -> None:
        """GET /api/job/status"""
        with _job_lock:
            status = dict(_job_progress)

        if not status:
            status = {
                "running": False,
                "progress": 0.0,
                "frames_done": 0,
                "total_frames": None,
                "error": None,
                "timestamp": datetime.now().isoformat(),
                "message": "No job running",
            }

        # Ensure all expected keys are present
        status.setdefault("running", False)
        status.setdefault("progress", 0.0)
        status.setdefault("frames_done", 0)
        status.setdefault("total_frames", None)
        status.setdefault("error", None)
        status.setdefault("timestamp", datetime.now().isoformat())
        status.setdefault("message", "")

        self._send_json(200, status)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, payload: str, status: int = 200) -> None:
        content = payload.encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionAbortedError, BrokenPipeError):
            pass  # cliente desconectado, no podemos hacer nada
