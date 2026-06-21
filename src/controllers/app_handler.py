# src/controllers/app_handler.py
import json
import uuid
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import cv2
import numpy as np

from src.models.contracts import ROIConfig, VideoSourceConfig
from src.models.enums import SourceType
from src.repositories.video_source_repo import VideoSourceRepository
from src.services.analytics_service import AnalyticsService
from src.services.report_service import generate_report_html
from src.utils.html_utils import render_home


BASE_DIR = Path(__file__).resolve().parent.parent

_repo = VideoSourceRepository()


def _load_video_sources() -> list[tuple[VideoSourceConfig, list[ROIConfig]]]:
    try:
        return _repo.get_all_with_rois()
    except Exception:
        return []


def _source_to_dict(src: VideoSourceConfig, rois: list[ROIConfig]) -> dict:
    return {
        "id": src.id,
        "name": src.name,
        "source_type": src.source_type.value,
        "source_uri": src.source_uri,
        "is_live": src.is_live,
        "rois": [
            {
                "id": r.id,
                "name": r.name,
                "polygon": r.polygon,
                "positive_label": r.positive_label,
                "negative_label": r.negative_label,
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

            cap = cv2.VideoCapture(uri)
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

        # API
        if parsed.path == "/api/sources":
            self._api_sources()
            return

        if parsed.path.startswith("/api/sources/"):
            parts = parsed.path.removeprefix("/api/sources/").split("/", 1)
            source_id = parts[0]
            if len(parts) == 2 and parts[1] == "preview":
                self._api_source_preview(source_id)
                return

        # Pages
        if parsed.path == "/":
            self._send_html(render_home())
            return

        if parsed.path.startswith("/files/"):
            rel = parsed.path.removeprefix("/files/")
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/sources":
            self._handle_create_source()
        elif parsed.path == "/process":
            self._handle_process()
        else:
            self.send_error(404)

    def _handle_process(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8")
        form = parse_qs(payload)
        video_source_id = form.get("video_source_id", [""])[0]
        output_video = form.get("output_video", [""])[0] == "on"

        try:
            config = _repo.get_by_id(video_source_id)
            if config is None:
                raise ValueError(f"Video source not found: {video_source_id}")
            rois = _repo.get_rois_for_source(video_source_id)

            service = AnalyticsService(config, rois)
            result = service.process(write_video=output_video, extra_analysis=None)
            report_html = generate_report_html(result)
            self._send_html(report_html)
        except Exception as exc:
            self._send_html(
                f"<html><body style='font-family:sans-serif;padding:40px'>"
                f"<h2 style='color:#dc2626'>Error</h2>"
                f"<p>{exc}</p>"
                f"<a href='/' style='color:var(--accent,#0f766e)'>Back to Dashboard</a>"
                f"</body></html>",
                status=500,
            )

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
