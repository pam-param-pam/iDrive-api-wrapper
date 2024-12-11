import logging
from typing import Union, Optional

from models.Item import Item
from utils.networker import make_request

logger = logging.getLogger("iDrive")

class File(Item):

    def __init__(self, file_id):
        super().__init__(file_id)
        self._thumbnail_url: Optional[str] = None
        self._size: Optional[int] = None
        self._extension: Optional[str] = None
        self._type: Optional[str] = None
        self._encryption_method: Optional[int] = None
        self._download_url: Optional[str] = None
        self._thumbnail_url: Optional[str] = None
        self._video_position: Optional[int] = None

        self._preview_url: Optional[str] = None
        self._iso: Optional[str] = None
        self._model_name: Optional[str] = None
        self._aperture: Optional[str] = None
        self._exposure_time: Optional[str] = None
        self._focal_length: Optional[str] = None

        self.isDir = False

    @property
    def thumbnail_url(self):
        if not (self._fetched or self._thumbnail_url):
            self._fetch_data()
        return self._thumbnail_url

    @property
    def size(self):
        if not (self._fetched or self._size):
            self._fetch_data()
        return self._size

    @property
    def view_url(self):
        return self.download_url + "?inline=True"

    @property
    def extension(self):
        if not (self._fetched or self._extension):
            self._fetch_data()
        return self._extension

    @property
    def type(self):
        if not (self._fetched or self._type):
            self._fetch_data()
        return self._type

    @property
    def encryption_method(self):
        if not (self._fetched or self._encryption_method):
            self._fetch_data()
        return self._encryption_method

    @property
    def download_url(self):
        if not (self._fetched or self._download_url):
            self._fetch_data()
        return self._download_url

    @property
    def video_position(self):
        if not (self._fetched or self._video_position):
            self._fetch_data()
        return self._video_position

    @property
    def iso(self):
        if not (self._fetched or self._iso):
            self._fetch_data()
        return self._iso

    @property
    def aperture(self):
        if not (self._fetched or self._aperture):
            self._fetch_data()
        return self._aperture

    @property
    def exposure_time(self):
        if not (self._fetched or self._exposure_time):
            self._fetch_data()
        return self._exposure_time

    @property
    def focal_length(self):
        if not (self._fetched or self._focal_length):
            self._fetch_data()
        return self._focal_length

    @property
    def preview_url(self):
        if not (self._fetched or self._preview_url):
            self._fetch_data()
        return self._preview_url

    @property
    def secrets(self):
        # todo
        return None



    def __str__(self):
        return f"File({self.name})"

    def _fetch_data(self):
        data = make_request("GET", f"file/{self.id}", headers=self._get_password_header())
        self._set_data(data)
        self._fetched = True



    def _set_data(self, json_data: dict):
        for key, value in json_data.items():
            if key == "isDir":
                self.isDir = value
            elif key == "id":
                self._id = value
            elif key == "name":
                self._name = value
            elif key == "parent_id":
                self._parent_id = value
            elif key == "created":
                self._created = value
            elif key == "last_modified":
                self._last_modified = value
            elif key == "isLocked":
                self._is_locked = value
            elif key == "lockFrom":
                self._lock_from = value
            elif key == "in_trash_since":
                self._in_trash_since = value
            elif key == "size":
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
            else:
                logger.warning(f"[FILE] Unexpected key: {key}")
