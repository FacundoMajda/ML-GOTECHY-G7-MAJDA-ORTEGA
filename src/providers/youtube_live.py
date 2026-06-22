# src/providers/youtube_live.py
from typing import Optional

import cv2
import numpy as np

from src.providers.base import FrameProvider
from src.providers.youtube_utils import extract_stream_url


class YouTubeLiveProvider(FrameProvider):
    MAX_RETRIES = 5
    RETRY_DELAY = 3  # seconds

    def __init__(self, url: str):
        print(f"[DEBUG] YouTubeLiveProvider.__init__: ENTRY url={url[:80]}...", flush=True)
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
        try:
            return extract_stream_url(self._url)
        except Exception as e:
            raise RuntimeError(
                f"No se pudo obtener el stream URL de {self._url}: {e}"
            )

    def _connect(self) -> None:
        print(f"[DEBUG] YouTubeLiveProvider._connect: connecting...", flush=True)
        self._stream_url = self._get_stream_url()
        print(f"[DEBUG] YouTubeLiveProvider._connect: got stream_url={self._stream_url[:80]}...", flush=True)
        self._cap = cv2.VideoCapture(self._stream_url)
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir stream live: {self._url}")
        self._fps = self._cap.get(cv2.CAP_PROP_FPS)
        self._connected = True
        print(f"[DEBUG] YouTubeLiveProvider._connect: connected, fps={self._fps}", flush=True)

    def _reconnect(self) -> bool:
        print(f"[DEBUG] YouTubeLiveProvider._reconnect: trying to reconnect...", flush=True)
        import time
        for attempt in range(self.MAX_RETRIES):
            try:
                self._cap.release()
                self._stream_url = self._get_stream_url()
                self._cap = cv2.VideoCapture(self._stream_url)
                if self._cap.isOpened():
                    self._connected = True
                    print(f"[DEBUG] YouTubeLiveProvider._reconnect: reconnected on attempt {attempt+1}", flush=True)
                    return True
            except Exception:
                time.sleep(self.RETRY_DELAY * (attempt + 1))
        print(f"[DEBUG] YouTubeLiveProvider._reconnect: failed after {self.MAX_RETRIES} attempts", flush=True)
        return False

    def next_frame(self) -> Optional[np.ndarray]:
        if self._cap is None:
            print(f"[DEBUG] YouTubeLiveProvider.next_frame: _cap is None, returning None", flush=True)
            return None

        ret, frame = self._cap.read()
        if not ret:
            self._connected = False
            print(f"[DEBUG] YouTubeLiveProvider.next_frame: read failed, trying reconnect", flush=True)
            if not self._reconnect():
                print(f"[DEBUG] YouTubeLiveProvider.next_frame: reconnect failed, returning None", flush=True)
                return None
            ret, frame = self._cap.read()
            if not ret:
                print(f"[DEBUG] YouTubeLiveProvider.next_frame: post-reconnect read failed, returning None", flush=True)
                return None

        self._frame_count += 1
        print(f"[DEBUG] YouTubeLiveProvider.next_frame: frame_count={self._frame_count} shape={frame.shape}", flush=True)
        return frame

    def get_fps(self) -> Optional[float]:
        result = self._fps if self._fps > 0 else None
        print(f"[DEBUG] YouTubeLiveProvider.get_fps: returning {result}", flush=True)
        return result

    def get_total_frames(self) -> Optional[int]:
        print(f"[DEBUG] YouTubeLiveProvider.get_total_frames: returning None (live)", flush=True)
        return None  # Live stream, unknown duration

    @property
    def is_live(self) -> bool:
        return True

    def release(self) -> None:
        print(f"[DEBUG] YouTubeLiveProvider.release: ENTRY", flush=True)
        if self._cap:
            self._cap.release()
            self._cap = None
        self._connected = False
        print(f"[DEBUG] YouTubeLiveProvider.release: released", flush=True)
