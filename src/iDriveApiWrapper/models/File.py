import logging
import os
from typing import Optional

from overrides import overrides

from .Enums import EncryptionMethod
from .Moment import Moment
from .Subtitle import Subtitle
from .VideoMetadata import VideoMetadata
from ..models.Item import Item
from ..utils.decorators import autoFetchProperty
from ..utils.networker import make_request

logger = logging.getLogger("iDrive")


class File(Item):

    def __init__(self, file_id):
        super().__init__(file_id)
        # _fetch_data
        self._thumbnail_url: Optional[str] = None
        self._size: Optional[int] = None
        self._extension: Optional[str] = None
        self._type: Optional[str] = None
        self._encryption_method: Optional[int] = None
        self._download_url: Optional[str] = None
        self._video_position: Optional[int] = None
        self._duration: Optional[int] = None
        self._tags: Optional[list[str]] = None
        self._crc: Optional[int] = None
        self._preview_url: Optional[str] = None
        self._iso: Optional[str] = None
        self._model_name: Optional[str] = None
        self._aperture: Optional[str] = None
        self._exposure_time: Optional[str] = None
        self._focal_length: Optional[str] = None

        # _fetch_more_data
        self._videoMetadata: Optional[dict] = None

        # _fetch_secrets
        self._encryption_iv: Optional[str] = None
        self._encryption_key: Optional[str] = None

        # _fetch_moments
        self._moments: Optional[list[Moment]] = None

        # _fetch_subtitles
        self._subtitles: Optional[list[Subtitle]] = None

    @property
    def view_url(self):
        return self.download_url + "?inline=True"

    @property
    @autoFetchProperty('_fetch_data')
    def thumbnail_url(self):
        return self._thumbnail_url

    @property
    @autoFetchProperty('_fetch_data')
    def size(self):
        return self._size

    @property
    @autoFetchProperty('_fetch_data')
    def extension(self):
        return self._extension

    @property
    @autoFetchProperty('_fetch_data')
    def type(self):
        return self._type

    @property
    @autoFetchProperty('_fetch_data')
    def encryption_method(self):
        return EncryptionMethod(self._encryption_method)

    @property
    @autoFetchProperty('_fetch_data')
    def download_url(self):
        return self._download_url

    @property
    @autoFetchProperty('_fetch_data')
    def video_position(self):
        return self._video_position

    @property
    @autoFetchProperty('_fetch_data')
    def crc(self):
        return self._crc

    @property
    @autoFetchProperty('_fetch_data')
    def iso(self):
        return self._iso

    @property
    @autoFetchProperty('_fetch_data')
    def aperture(self):
        return self._aperture

    @property
    @autoFetchProperty('_fetch_data')
    def exposure_time(self):
        return self._exposure_time

    @property
    @autoFetchProperty('_fetch_data')
    def focal_length(self):
        return self._focal_length

    @property
    @autoFetchProperty('_fetch_data')
    def preview_url(self):
        return self._preview_url

    @property
    @autoFetchProperty('_fetch_data')
    def duration(self):
        return self._duration

    @property
    @autoFetchProperty('_fetch_data')
    def tags(self):
        # todo
        pass

    @property
    @autoFetchProperty('_fetch_data')
    def isVideoMetadata(self):
        return self._isVideoMetadata

    @property
    @autoFetchProperty('_fetch_more_data')
    def videoMetadata(self) -> VideoMetadata:
        return VideoMetadata(self._videoMetadata)

    @property
    @autoFetchProperty('_fetch_secrets')
    def encryption_iv(self):
        return self._encryption_iv

    @property
    @autoFetchProperty('_fetch_secrets')
    def encryption_key(self):
        return self._encryption_key

    @property
    @autoFetchProperty('_fetch_moments')
    def moments(self):
        return self._moments

    @property
    @autoFetchProperty('_fetch_subtitles')
    def subtitles(self):
        return self._subtitles

    def __str__(self):
        return f"File({self.name})"

    def __repr__(self):
        return str(self)

    @overrides
    def _set_more_data(self, data):
        self._videoMetadata = data

    @overrides
    def _fetch_data(self):
        data = make_request("GET", f"files/{self.id}", headers=self._get_password_header())
        self._set_data(data)

    def _fetch_moments(self):
        data = make_request("GET", f"files/{self.id}/moments", headers=self._get_password_header())
        self._moments = []
        for element in data:
            moment = Moment(**element)
            if self.get_password():
                moment.set_password(self.get_password())
            self._moments.append(Moment(**element))

    def _fetch_subtitles(self):
        data = make_request("GET", f"files/{self.id}/subtitles", headers=self._get_password_header())
        self._subtitles = []
        for element in data:
            subtitle = Subtitle(**element)
            if self.get_password():
                subtitle.set_password(self.get_password())
            self._subtitles.append(subtitle)

    def create_moment(self, timestamp):
        raise NotImplemented()
        # todo
        data = {"timestamp": 73, "file_id": "9FbHJVrVSV2zF3BFE4Xxch", "size": 25397, "message_id": "1354806011386400962", "attachment_id": "1354806011499905086",
                "message_author_id": "1344677807225311283"}
        data = make_request("POST", f"files/moment/add", headers=self._get_password_header())

    def play(self):
        if self.type != "video":
            raise ValueError("File is not a video")
        os.system(f"ffplay -i {self.download_url}")

    def _fetch_secrets(self):
        data = make_request("GET", f"file/secrets/{self.id}", headers=self._get_password_header())
        self._encryption_key = data['key']
        self._encryption_iv = data['iv']

    @overrides
    def download(self, folder_path="", callback=None) -> str:
        from ..utils.common import download_from_url
        return download_from_url(self.download_url, folder_path)

    @overrides
    def _set_data(self, json_data: dict) -> None:
        json_data = super()._set_data(json_data)
        for key, value in json_data.items():
            if key == "size":
                self._size = value
            elif key == "extension":
                self._extension = value
            elif key == "type":
                self._type = value
            elif key == "encryption_method":
                self._encryption_method = value
            elif key == "video_position":
                self._video_position = value
            elif key == "thumbnail_url":
                self._thumbnail_url = value
            elif key == "download_url":
                self._download_url = value
            elif key == "preview_url":
                self._preview_url = value
            elif key == "iso":
                self._iso = value
            elif key == "model_name":
                self._model_name = value
            elif key == "aperture":
                self._aperture = value
            elif key == "exposure_time":
                self._exposure_time = value
            elif key == "focal_length":
                self._focal_length = value
            elif key == "tags":
                self._tags = value
            elif key == "duration":
                self._duration = value
            elif key == "isVideoMetadata":
                self._isVideoMetadata = value
            elif key == "crc":
                self._crc = value
            else:
                logger.warning(f"[FILE] Unexpected key: {key}")
