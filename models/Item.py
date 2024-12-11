from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from models.baseResource import Resource
from utils.networker import make_request

if TYPE_CHECKING:
    from Folder import Folder


class Item(Resource, ABC):

    def __init__(self, item_id):
        from models import Folder
        super().__init__(item_id)
        self._name: Optional[str] = None
        self._parent_id: Optional[str] = None
        self._created: Optional[str] = None
        self._last_modified: Optional[str] = None
        self._lock_from: Optional[str] = None
        self._is_locked: Optional[bool] = None
        self._in_trash_since: Optional[str] = None
        self._parent: Optional[Folder] = None

    def __repr__(self):
        return self.name

    @abstractmethod
    async def _fetch_data(self):
        raise NotImplementedError

    @abstractmethod
    async def download(self):
        raise NotImplementedError

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        if not (self._fetched or self._name):
            self._fetch_data()
        return self._name

    @property
    def parent(self):
        from models.Folder import Folder

        if self._fetched:
            self._fetch_data()
        if not self._parent_id:
            raise ValueError("Root folder has no parent!")
        if not self._parent:
            self._parent = Folder(self._parent_id)
        return self._parent

    @property
    def created(self):
        if not (self._fetched or self._created):
            self._fetch_data()
        return self._created

    @property
    def last_modified(self):
        if not (self._fetched or self._last_modified):
            self._fetch_data()
        return self._last_modified

    @property
    def is_locked(self):
        if not (self._fetched or self._is_locked):
            self._fetch_data()
        return self._is_locked

    @property
    def lock_from(self):
        if not (self._fetched or self._lock_from):
            self._fetch_data()
        return self._lock_from

    @property
    def in_trash_since(self):
        if not (self._fetched or self._in_trash_since):
            self._fetch_data()
        return self._in_trash_since

    @abstractmethod
    def _set_data(self, json_data: dict):
        raise NotImplementedError

    async def rename(self, new_name: str) -> None:
        await make_request("PATCH", f"item/rename", {'id': self.id, 'new_name': new_name}, headers=self._get_password_header())

    async def move_to_trash(self) -> None:
        from utils import common
        await common.move_to_trash([self])

    async def delete(self) -> None:
        from utils import common
        await common.move_to_trash([self])

    async def restore_from_trash(self) -> None:
        from utils import common
        await common.move_to_trash([self])

    async def move(self, new_parent: Folder) -> None:
        from utils import common
        await common.move([self], new_parent)
