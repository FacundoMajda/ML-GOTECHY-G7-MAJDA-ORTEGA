from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.providers.base import FrameProvider


class LocalFileProvider(FrameProvider):
    def __init__(self, file_path: str):
        print(f"[DEBUG] LocalFileProvider.__init__: ENTRY file_path={file_path}", flush=True)
        self._path = Path(file_path)
        self._cap = cv2.VideoCapture(str(self._path))
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir el video: {file_path}")
        print(f"[DEBUG] LocalFileProvider.__init__: VideoCapture opened successfully", flush=True)

    def next_frame(self) -> Optional[np.ndarray]:
        ret, frame = self._cap.read()
        if not ret:
            print(f"[DEBUG] LocalFileProvider.next_frame: end of video, returning None", flush=True)
            return None
        print(f"[DEBUG] LocalFileProvider.next_frame: returned frame shape={frame.shape}", flush=True)
        return frame

    def get_fps(self) -> Optional[float]:
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        result = float(fps) if fps > 0 else None
        print(f"[DEBUG] LocalFileProvider.get_fps: returning {result}", flush=True)
        return result

    def get_total_frames(self) -> Optional[int]:
        frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        result = frames if frames > 0 else None
        print(f"[DEBUG] LocalFileProvider.get_total_frames: returning {result}", flush=True)
        return result

    @property
    def is_live(self) -> bool:
        return False

    def release(self) -> None:
        print(f"[DEBUG] LocalFileProvider.release: ENTRY", flush=True)
        self._cap.release()
        print(f"[DEBUG] LocalFileProvider.release: released", flush=True)
