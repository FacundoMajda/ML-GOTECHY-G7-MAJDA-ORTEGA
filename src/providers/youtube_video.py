# src/providers/youtube_video.py
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import yt_dlp

from src.providers.base import FrameProvider


class YouTubeVideoProvider(FrameProvider):
    def __init__(self, url: str):
        self._url = url
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_live = False
        self._fps: Optional[float] = None
        self._total_frames: Optional[int] = None
        self._connect()

    def _connect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "best[ext=mp4]/best",
                "outtmpl": f"{tmpdir}/video.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self._url, download=True)
            except Exception as e:
                raise RuntimeError(
                    f"No se pudo descargar el video {self._url}: {e}"
                )
            if info is None:
                raise RuntimeError(f"No se pudo obtener info de {self._url}")
            filename = ydl.prepare_filename(info)
            self._fps = info.get("fps")
            self._total_frames = info.get("duration", 0)
            if self._fps:
                self._total_frames = int(info["duration"] * self._fps)

        self._cap = cv2.VideoCapture(filename)

    def next_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def get_fps(self) -> Optional[float]:
        return self._fps

    def get_total_frames(self) -> Optional[int]:
        return self._total_frames

    @property
    def is_live(self) -> bool:
        return self._is_live

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
