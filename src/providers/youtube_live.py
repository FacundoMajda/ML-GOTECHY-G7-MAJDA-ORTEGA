# src/providers/youtube_live.py
import tempfile
from typing import Optional

import cv2
import numpy as np
import yt_dlp

from src.providers.base import FrameProvider


class YouTubeLiveProvider(FrameProvider):
    MAX_RETRIES = 5
    RETRY_DELAY = 3  # seconds

    def __init__(self, url: str):
        self._url = url
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_live = True
        self._fps: Optional[float] = None
        self._total_frames: Optional[int] = None
        self._frame_count = 0
        self._connected = False
        self._stream_url: Optional[str] = None
        self._connect()

    def _get_stream_url(self) -> str:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self._url, download=False)
                return info["url"]
        except Exception as e:
            raise RuntimeError(
                f"No se pudo obtener el stream URL de {self._url}: {e}"
            )

    def _connect(self) -> None:
        self._stream_url = self._get_stream_url()
        self._cap = cv2.VideoCapture(self._stream_url)
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir stream live: {self._url}")
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._connected = True

    def _reconnect(self) -> bool:
        for attempt in range(self.MAX_RETRIES):
            try:
                self._cap.release()
                self._stream_url = self._get_stream_url()
                self._cap = cv2.VideoCapture(self._stream_url)
                if self._cap.isOpened():
                    self._connected = True
                    return True
            except Exception:
                import time
                time.sleep(self.RETRY_DELAY * (attempt + 1))
        return False

    def next_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            return None

        ret, frame = self._cap.read()
        if not ret:
            self._connected = False
            if not self._reconnect():
                return None
            ret, frame = self._cap.read()
            if not ret:
                return None

        self._frame_count += 1
        return frame

    def get_fps(self) -> Optional[float]:
        return self._fps if self._fps > 0 else None

    def get_total_frames(self) -> Optional[int]:
        return None  # Live stream, unknown duration

    @property
    def is_live(self) -> bool:
        return True

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
        self._connected = False
