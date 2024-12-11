import asyncio
import logging
from typing import Union, List

from Config import APIConfig
from models.Item import Item
from models.ItemsList import ItemsList
from models.File import File
from models.Folder import Folder
from models.User import User
from utils import common
from utils.networker import make_request

# Create a custom logger
logger = logging.getLogger("iDrive")
logger.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set handler level to DEBUG

# Define a formatter and attach it to the handler
formatter = logging.Formatter("%(name)s: %(message)s")
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)


class Client:
    def __init__(self, token: str):
        # self.auth = AuthManager(token)
        # self.token = self.auth.get_access_token()
        self._token = token
        self._user: Union[User, None] = None
        APIConfig.token = token
        asyncio.run(self._fetch_user())

        APIConfig.user = self._user

    @staticmethod
    async def login(username: str, password: str) -> str:
        data = await make_request("POST", "auth/token/login", data={'username': username, 'password': password})
        return data['auth_token']

    async def _fetch_user(self) -> None:
        data = await make_request("GET", "auth/user/me")
        self.user = User(data)

    async def get_root(self):
        return Folder(self.user.root_id)

    async def search(self, query: str, files: bool = True, folders: bool = True, type: str = "", extension: str = "", max_results: int = 50) -> ItemsList:
        data = await make_request("GET", "search", params={"query": query, "files": files, "folder": folders, "type": type, "extension": extension, "resultsLimit": max_results})
        return Folder._parse_children(None, data)

    async def get_trash(self) -> Union[List[Union[Folder, File]], None]:
        data = await make_request("GET", "trash")
        data = data['trash']
        return Folder._parse_children(None, data)

    async def get_file(self, file_id) -> File:
        file = File(file_id)
        await file._fetch_data()
        return file

    async def get_folder(self, folder_id) -> Folder:
        folder = Folder(folder_id)
        await folder._fetch_data()
        return folder

    def set_download_path(self, path: str):
        APIConfig.default_path = path

    async def move_to_trash(self, items: List[Item]):
        await common.move_to_trash(items)

    async def restore_from_trash(self, items: List[Item]):
        await common.restore_from_trash(items)

    async def delete(self, items: List[Item]):
        await common.delete(items)

    async def move(self, items: List[Item], new_parent: Folder):
        await common.move(items, new_parent)

    async def download(self, items: List[Item], callback=None):
        download_url = await common.get_zip_download_url(items)
        await common.download_from_url(download_url)
