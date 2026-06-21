from enum import Enum


class SourceType(str, Enum):
    FILE = "file"
    YOUTUBE_VOD = "youtube_vod"
    YOUTUBE_LIVE = "youtube_live"
    RTSP = "rtsp"


class TimestampMode(str, Enum):
    FRAME_BASED = "frame_based"
    REALTIME = "realtime"


class EventType(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    OVERCAPACITY = "overcapacity"
    DWELL_EXCEEDED = "dwell_exceeded"
