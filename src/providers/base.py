from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class FrameProvider(ABC):
    @abstractmethod
    def next_frame(self) -> Optional[np.ndarray]:
        """Retorna el proximo frame, o None si termino/perdio conexion."""
        ...

    @abstractmethod
    def get_fps(self) -> Optional[float]:
        """None para streams live."""
        ...

    @abstractmethod
    def get_total_frames(self) -> Optional[int]:
        """None para streams live."""
        ...

    @property
    @abstractmethod
    def is_live(self) -> bool:
        ...

    @abstractmethod
    def release(self) -> None:
        ...
