from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VideoTrack:
    bitrate: Optional[float]
    codec: Optional[str]
    size: int
    duration: Optional[int]
    language: Optional[str]
    height: Optional[int]
    width: Optional[int]
    fps: Optional[float]
    track_number: int


@dataclass
class AudioTrack:
    bitrate: Optional[float]
    codec: Optional[str]
    size: Optional[int]
    duration: Optional[float]
    language: Optional[str]
    name: Optional[str]
    channel_count: Optional[int]
    sample_rate: Optional[int]
    sample_size: Optional[int]
    track_number: int


@dataclass
class SubtitleTrack:
    bitrate: Optional[float]
    codec: Optional[str]
    size: Optional[int]
    duration: Optional[int]
    language: Optional[str]
    name: Optional[str]
    track_number: int


@dataclass
class VideoMetadata:
    mime: str
    is_progressive: bool
    is_fragmented: bool
    has_moov: bool
    has_IOD: bool
    brands: Optional[str]
    video_tracks: List[VideoTrack]
    audio_tracks: List[AudioTrack]
    subtitle_tracks: List[SubtitleTrack]

