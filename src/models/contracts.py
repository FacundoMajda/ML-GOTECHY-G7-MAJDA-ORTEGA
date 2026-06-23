from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.models.enums import EventType, SourceType, TimestampMode


@dataclass
class ROIConfig:
    id: str
    name: str
    polygon: list[list[int]]  # [[x1,y1],[x2,y2],...]
    positive_label: str = "inside"
    negative_label: str = "outside"
    detect_entry: bool = True
    detect_exit: bool = True
    detect_occupancy: bool = True
    detect_dwell: bool = False
    alerts: list = field(default_factory=list)  # list[dict] — JSONB from DB


@dataclass
class VideoSourceConfig:
    id: str
    name: str
    source_type: SourceType
    source_uri: str
    is_live: bool


@dataclass
class TrackedEntityRecord:
    track_id: int
    first_seen_at: datetime
    last_seen_at: datetime
    first_seen_frame: Optional[int] = None
    last_seen_frame: Optional[int] = None
    object_class: str = "person"


@dataclass
class OccupancySnapshot:
    roi_id: str
    captured_at: datetime
    frame_number: Optional[int]
    count_inside: int
    count_outside: int
    track_ids_inside: list[int]
    object_class_counts: dict = field(default_factory=dict)


@dataclass
class ZoneEventRecord:
    roi_id: str
    event_type: EventType
    occurred_at: datetime
    track_id: Optional[int] = None
    frame_number: Optional[int] = None
    dwell_seconds: Optional[float] = None
    object_class: str = "person"
    metadata: dict = field(default_factory=dict)


@dataclass
class EventRuleConfig:
    id: str
    roi_id: str
    event_type: EventType
    threshold: Optional[int] = None


@dataclass
class SessionResult:
    video_source_id: str
    timestamp_mode: TimestampMode
    started_at: datetime
    ended_at: Optional[datetime]
    fps: Optional[float]
    total_frames: Optional[int]
    write_video: bool
    output_video_path: Optional[str]
    extra_analysis: Optional[dict]
    tracked_entities: list[TrackedEntityRecord] = field(default_factory=list)
    occupancy_snapshots: list[OccupancySnapshot] = field(default_factory=list)
    zone_events: list[ZoneEventRecord] = field(default_factory=list)
    id: Optional[str] = None


@dataclass
class ROIAlert:
    alert_type: str  # Literal["overcapacity", "dwell_exceeded", "area_empty"]
    threshold: int


@dataclass
class ROIAnalyticsConfig:
    roi_id: str
    detect_entry: bool = True
    detect_exit: bool = True
    detect_occupancy: bool = True
    detect_dwell: bool = False
    alerts: list[ROIAlert] = field(default_factory=list)


@dataclass
class SourceAnalyticsConfig:
    tracking_classes: list[str] = field(default_factory=lambda: ["person"])
    frame_skip: int = 1
    max_seconds: int | None = None
    global_alerts: list = field(default_factory=list)
