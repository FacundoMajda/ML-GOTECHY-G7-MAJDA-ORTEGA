# src/providers/youtube_video.py
from typing import Optional

import cv2
import numpy as np

from src.providers.base import FrameProvider
from src.providers.youtube_utils import extract_stream_url, extract_youtube_info


class YouTubeVideoProvider(FrameProvider):
    def __init__(self, url: str):
        print(f"[DEBUG] YouTubeVideoProvider.__init__: ENTRY url={url[:80]}...", flush=True)
        self._url = url
        self._cap: Optional[cv2.VideoCapture] = None
        self._is_live = False
        self._fps: Optional[float] = None
        self._total_frames: Optional[int] = None
        self._connect()

    def _connect(self) -> None:
        print(f"[DEBUG] YouTubeVideoProvider._connect: resolving YouTube URL...", flush=True)
        try:
            info = extract_youtube_info(self._url, download=False)
            stream_url = extract_stream_url(self._url)
        except Exception as exc:
            raise RuntimeError(
                f"No se pudo abrir el video de YouTube {self._url}: {exc}"
            ) from exc

        self._fps = info.get("fps")
        duration = info.get("duration")
        self._total_frames = int(duration * self._fps) if duration and self._fps else None
        print(f"[DEBUG] YouTubeVideoProvider._connect: fps={self._fps} total_frames={self._total_frames}", flush=True)

        self._cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir stream VOD de YouTube: {self._url}")
        print(f"[DEBUG] YouTubeVideoProvider._connect: VideoCapture opened", flush=True)

    def next_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            print(f"[DEBUG] YouTubeVideoProvider.next_frame: _cap is None, returning None", flush=True)
            return None
        ret, frame = self._cap.read()
        if not ret:
            print(f"[DEBUG] YouTubeVideoProvider.next_frame: end of stream, returning None", flush=True)
            return None
        print(f"[DEBUG] YouTubeVideoProvider.next_frame: returned frame shape={frame.shape}", flush=True)
        return frame

    def get_fps(self) -> Optional[float]:
        print(f"[DEBUG] YouTubeVideoProvider.get_fps: returning {self._fps}", flush=True)
        return self._fps

    def get_total_frames(self) -> Optional[int]:
        print(f"[DEBUG] YouTubeVideoProvider.get_total_frames: returning {self._total_frames}", flush=True)
        return self._total_frames

    @property
    def is_live(self) -> bool:
        return self._is_live

    def release(self) -> None:
        print(f"[DEBUG] YouTubeVideoProvider.release: ENTRY", flush=True)
        if self._cap:
            self._cap.release()
            self._cap = None
        print(f"[DEBUG] YouTubeVideoProvider.release: released", flush=True)
