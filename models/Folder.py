import logging

from typing import Union, Optional,TYPE_CHECKING

from models.Item import Item
from utils.networker import make_request

from models.File import File

logger = logging.getLogger("iDrive")

if TYPE_CHECKING:
    from models.ItemsList import ItemsList


class Folder(Item):
    def __init__(self, folder_id):
        super().__init__(folder_id)
        self._children: Optional[ItemsList] = None
        self._folder_size: Optional[Folder] = None
        self._file_count: Optional[Folder] = None
        self._folder_count: Optional[Folder] = None
        self.isDir = True

    @property
    def children(self):
        if not (self._fetched or self._children):
            self._fetch_data()
        return self._children

    @property
    def folder_size(self):
        if not self._folder_size:
            self._fetch_more_info()
        return self._folder_size

    @property
    def file_count(self):
        if not self._file_count:
            self._fetch_more_info()
        return self._file_count

    @property
    def folder_count(self):
        if not self._folder_count:
            self._fetch_more_info()
        return self._folder_count

    def __str__(self):
        return f"Folder({self.name})"

    def _fetch_more_info(self):
        data = make_request("GET", f"folder/moreinfo/{self.id}", headers=self._get_password_header())
        self._folder_size = data['folder_size']
        self._folder_count = data['folder_count']
        self._file_count = data['file_count']

    def _fetch_data(self):
        data = make_request("GET", f"folder/{self.id}", headers=self._get_password_header())
        self._set_data(data['folder'])
        self._fetched = True

    def upload(self):
        pass

    def download(self, callback=None):
        from utils.common import get_zip_download_url, download_from_url
        download_url = get_zip_download_url([self])

        download_from_url(download_url)

    @staticmethod
    def _parse_children(parent: Union['Folder', None], data: dict):
        from models.ItemsList import ItemsList

        children = []
        for element in data:
            if element['isDir']:
                item = Folder(element['id'])
            else:
                item = File(element['id'])

            item._set_data(element)

            if parent and parent._password:
                item.set_password(parent._password)
            children.append(item)

        return ItemsList(children)

    def _set_data(self, json_data: dict):
        for key, value in json_data.items():
            if key == "isDir":
                self.isDir = value
            elif key == "id":
                self._id = value
            elif key == "name":
                self._name = value
            elif key == "parent_id":
                self._parent_id = key
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
            elif key == "children":
                self._children = self._parse_children(self, value)
            else:
                logger.warning(f"[FOLDER] Unexpected renderer: {key}")

