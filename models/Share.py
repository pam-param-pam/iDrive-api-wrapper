# import logging
#
# from models.Folder import Folder
# from models.baseResource import Resource
# from utils.decorators import overrides
#
# logger = logging.getLogger("iDrive")
# import logging
#
# from typing import Union, Optional, TYPE_CHECKING
#
# from models.Item import Item
#
# from models.File import File
#
# logger = logging.getLogger("iDrive")
#
# if TYPE_CHECKING:
#     from models.ItemsList import ItemsList
#
#
# class Folder(Item):
#     def __init__(self, folder_id):
#         super().__init__(folder_id)
#         self._children: Optional[ItemsList] = None
#
#         self._name: Optional[str] = None
#         self._parent_id: Optional[str] = None
#         self._created: Optional[str] = None
#         self._last_modified: Optional[str] = None
#         self._parent: Optional[Folder] = None
#         self._id: str = folder_id
#         self.isDir = True
#
#     def __str__(self):
#         return f"ShareFolder({self.name})"
#
#     def _parse_children(self, parent: Union['Folder', None], data: dict):
#         from models.ItemsList import ItemsList
#
#         children = []
#         for element in data:
#             if element['isDir']:
#                 item = Folder(element['id'])
#             else:
#                 item = File(element['id'])
#
#             item._set_data(element)
#
#             if parent and parent._password:
#                 item.set_password(parent._password)
#             children.append(item)
#
#         return ItemsList(children)
#
#     def _set_data(self, json_data: dict):
#         for key, value in json_data.items():
#             if key == "isDir":
#                 self.isDir = value
#             elif key == "id":
#                 self._id = value
#             elif key == "name":
#                 self._name = value
#             elif key == "parent_id":
#                 self._parent_id = key
#             elif key == "created":
#                 self._created = value
#             elif key == "last_modified":
#                 self._last_modified = value
#             elif key == "children":
#                 self._children = self._parse_children(self, value)
#             else:
#                 logger.warning(f"[FOLDER] Unexpected renderer: {key}")
#
#
# class ShareFolder(Folder):
#     def __init__(self, folder_id):
#         super().__init__(folder_id)
#         self._fetched = True
#
#     @overrides
#     def children(self):
#         pass
#
#
from typing import Optional

from iDrive import logger
from models.Resource import Resource


class Share(Resource):
    def __init__(self, share_id, token, expire):
        super().__init__(share_id)
        self.expire: Optional[str] = None
        self.token: Optional[str] = None

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
