from collections import namedtuple
from typing import NamedTuple, Optional

MomentTuple = namedtuple('Moment', ['file_id', 'timestamp', 'created_at', 'url'])


class VideoTrackTuple(NamedTuple):
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    language: Optional[str] = None
    number: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None
    fps: Optional[int] = None
    type: Optional[int] = None

class AudioTrackTuple(NamedTuple):
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    language: Optional[str] = None
    number: Optional[int] = None
    name: Optional[str] = None
    channel_count: Optional[int] = None
    sample_rate: Optional[int] = None
    sample_size: Optional[int] = None
    type: Optional[int] = None

class SubtitleTrackTuple(NamedTuple):
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    language: Optional[str] = None
    number: Optional[int] = None
    name: Optional[str] = None
    type: Optional[int] = None
