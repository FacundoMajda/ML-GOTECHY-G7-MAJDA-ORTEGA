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
        print(f"[DEBUG] VideoSourceFactory.create: ENTRY type={config.source_type.value} uri={str(config.source_uri)[:80]}...", flush=True)
        match config.source_type:
            case SourceType.FILE:
                provider = LocalFileProvider(config.source_uri)
            case SourceType.YOUTUBE_VOD:
                provider = YouTubeVideoProvider(config.source_uri)
            case SourceType.YOUTUBE_LIVE:
                provider = YouTubeLiveProvider(config.source_uri)
            case SourceType.RTSP:
                provider = RTSPProvider(config.source_uri)
            case _:
                raise NotImplementedError(
                    f"Source type {config.source_type} no implementado"
                )
        print(f"[DEBUG] VideoSourceFactory.create: returning {type(provider).__name__}", flush=True)
        return provider
