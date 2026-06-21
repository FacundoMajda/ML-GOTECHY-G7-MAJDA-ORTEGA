# src/providers/factory.py
from src.models.contracts import VideoSourceConfig
from src.models.enums import SourceType
from src.providers.base import FrameProvider
from src.providers.local_file import LocalFileProvider
from src.providers.rtsp import RTSPProvider
from src.providers.youtube_live import YouTubeLiveProvider
from src.providers.youtube_video import YouTubeVideoProvider


class VideoSourceFactory:
    @staticmethod
    def create(config: VideoSourceConfig) -> FrameProvider:
        match config.source_type:
            case SourceType.FILE:
                return LocalFileProvider(config.source_uri)
            case SourceType.YOUTUBE_VOD:
                return YouTubeVideoProvider(config.source_uri)
            case SourceType.YOUTUBE_LIVE:
                return YouTubeLiveProvider(config.source_uri)
            case SourceType.RTSP:
                return RTSPProvider(config.source_uri)
            case _:
                raise NotImplementedError(
                    f"Source type {config.source_type} no implementado"
                )
