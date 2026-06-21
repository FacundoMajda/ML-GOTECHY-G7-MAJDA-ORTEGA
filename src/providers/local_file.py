from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from src.providers.base import FrameProvider


class LocalFileProvider(FrameProvider):
    def __init__(self, file_path: str):
        self._path = Path(file_path)
        self._cap = cv2.VideoCapture(str(self._path))
        if not self._cap.isOpened():
            raise RuntimeError(f"No se pudo abrir el video: {file_path}")

    def next_frame(self) -> Optional[np.ndarray]:
        ret, frame = self._cap.read()
        if not ret:
            return None
        return frame

    def get_fps(self) -> Optional[float]:
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        return float(fps) if fps > 0 else None

    def get_total_frames(self) -> Optional[int]:
        frames = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return frames if frames > 0 else None

    @property
    def is_live(self) -> bool:
        return False

    def release(self) -> None:
        self._cap.release()
