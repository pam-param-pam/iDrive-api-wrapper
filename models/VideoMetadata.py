import logging
from typing import Optional

from models.namedTuples import VideoTrackTuple, AudioTrackTuple, SubtitleTrackTuple

logger = logging.getLogger("iDrive")

class VideoMetadata:

    def __init__(self, data):
        self._brands: Optional[str, None] = None
        self._mime: Optional[str, None] = None
        self._has_IOD: Optional[bool, None] = None
        self._has_moov: Optional[bool, None] = None
        self._is_progressive: Optional[bool, None] = None
        self._is_fragmented: Optional[bool, None] = None
        self._tracks: Optional[list, None] = None

        self._video_tracks = []
        self._audio_tracks = []
        self._subtitle_tracks = []
        self._set_data(data)


    @property
    def brands(self):
        return self._brands

    @property
    def mime(self):
        return self._mime

    @property
    def has_IOD(self):
        return self._has_IOD

    @property
    def has_moov(self):
        return self._has_moov

    @property
    def is_progressive(self):
        return self._is_progressive

    @property
    def is_fragmented(self):
        return self._is_fragmented

    @property
    def video_tracks(self):
        return self._video_tracks

    @property
    def subtitle_tracks(self):
        return self._subtitle_tracks

    @property
    def audio_tracks(self):
        return self._audio_tracks

    def _set_data(self, data):
        for key, value in data.items():
            if key == "brands":
                self._brands = value
            elif key == "mime":
                self._mime = value
            elif key == "mime":
                self._brands = value
            elif key == "has_IOD":
                self._has_IOD = value
            elif key == "has_moov":
                self._has_moov = value
            elif key == "is_progressive":
                self._is_progressive = value
            elif key == "is_fragmented":
                self._is_fragmented = value
            elif key == "brands":
                self._brands = value
            elif key == "tracks":
                self._set_tracks(value)
            else:
                logger.warning(f"[VideoMetadata] Unexpected renderer: {key}")

    def _set_tracks(self, tracks):
        self._tracks = tracks
        for track in tracks:
            if track['type'] == "Video":
                self._video_tracks.append(VideoTrackTuple(**track))
            elif track['type'] == "Audio":
                self._audio_tracks.append(AudioTrackTuple(**track))
            elif track['type'] == "Subtitle":
                self._subtitle_tracks.append(SubtitleTrackTuple(**track))
            else:
                logger.warning(f"[VideoMetadata] Unexpected renderer: {track['type']}")

    def __str__(self):
        return f"VideoMetadata[tracks={len(self._tracks)}]"
