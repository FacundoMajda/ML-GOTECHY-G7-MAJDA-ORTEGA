# src/providers/rtsp.py
from typing import Optional

import cv2
import numpy as np

from src.providers.base import FrameProvider


class RTSPProvider(FrameProvider):
    MAX_RETRIES = 5
    RETRY_DELAY = 2  # seconds

    def __init__(self, url: str):
        self._url = url
        self._cap: Optional[cv2.VideoCapture] = None
        self._fps: Optional[float] = None
        self._connected = False
        self._connect()

    def _connect(self) -> None:
        self._cap = cv2.VideoCapture(self._url)
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir RTSP: {self._url}")
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._connected = True

    def _reconnect(self) -> bool:
        import time
        for attempt in range(self.MAX_RETRIES):
            self._cap.release()
            self._cap = cv2.VideoCapture(self._url)
            if self._cap.isOpened():
                self._fps = self._cap.get(cv2.CAP_PROP_FPS)
                self._connected = True
                return True
            time.sleep(self.RETRY_DELAY * (attempt + 1))
        return False

    def next_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            return None

        ret, frame = self._cap.read()
        if not ret:
            if not self._reconnect():
                return None
            ret, frame = self._cap.read()
            if not ret:
                return None

        return frame

    def get_fps(self) -> Optional[float]:
        return self._fps if self._fps and self._fps > 0 else None

    def get_total_frames(self) -> Optional[int]:
        return None  # RTSP streams have unknown duration

    @property
    def is_live(self) -> bool:
        return True

    def release(self) -> None:
        if self._cap:
            self._cap.release()
            self._cap = None
        self._connected = False
