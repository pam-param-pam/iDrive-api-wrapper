import logging
from typing import Union, Optional, TYPE_CHECKING

from overrides import overrides

from .File import File
from .Item import Item
from ..utils.decorators import autoFetchProperty
from ..utils.networker import make_request

logger = logging.getLogger("iDrive")

if TYPE_CHECKING:
    from ..models.ItemsList import ItemsList


class Folder(Item):
    def __init__(self, folder_id):
        super().__init__(folder_id)
        self._children: Optional[ItemsList] = None
        self._folder_size: Optional[Folder] = None
        self._file_count: Optional[Folder] = None
        self._folder_count: Optional[Folder] = None

    @property
    @autoFetchProperty('_fetch_data')
    def children(self):
        return self._children

    @property
    @autoFetchProperty('_fetch_more_data')
    def folder_size(self):
        return self._folder_size

    @property
    @autoFetchProperty('_fetch_more_data')
    def file_count(self):
        return self._file_count

    @property
    @autoFetchProperty('_fetch_more_data')
    def folder_count(self):
        return self._folder_count

    def __str__(self):
        return f"Folder({self.name})"

    @overrides
    def _set_more_data(self, data) -> None:
        self._folder_size = data['folder_size']
        self._folder_count = data['folder_count']
        self._file_count = data['file_count']

    @overrides
    def _fetch_data(self) -> None:
        data = make_request("GET", f"folders/{self.id}", headers=self._get_password_header())
        self._set_data(data['folder'])
        self._fetched = True

    def lock_with_password(self, new_password) -> None:
        make_request("POST", f"folder/password/{self.id}", headers=self._get_password_header(), data={"new_password": new_password})
        self.set_password(new_password)

    def unlock(self) -> None:
        make_request("POST", f"folder/password/{self.id}", headers=self._get_password_header(), data={"new_password": ""})
        self.set_password(None)

    def upload(self):
        pass

    @overrides
    def download(self, callback=None) -> str:
        from ..utils.common import get_zip_download_url, download_from_url

        download_url = get_zip_download_url([self])
        return download_from_url(download_url)

    @staticmethod
    def _parse_children(parent: Union['Folder', None], data: dict):
        from ..models.ItemsList import ItemsList

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

    @overrides
    def _set_data(self, json_data: dict) -> None:
        json_data = super()._set_data(json_data)
        for key, value in json_data.items():
            if key == "children":
                self._children = self._parse_children(self, value)
            else:
                logger.warning(f"[FOLDER] Unexpected renderer: {key}")
