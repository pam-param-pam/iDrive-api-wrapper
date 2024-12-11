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
        self._fetch_user()
        APIConfig.user = self._user

    @staticmethod
    def login(username: str, password: str) -> str:
        data = make_request("POST", "auth/token/login", data={'username': username, 'password': password})
        return data['auth_token']

    def _fetch_user(self) -> None:
        data = make_request("GET", "auth/user/me")
        self.user = User(data)

    def get_root(self):
        return Folder(self.user.root_id)

    def search(self, query: str, files: bool = True, folders: bool = True, type: str = "", extension: str = "", max_results: int = 50) -> ItemsList:
        data = make_request("GET", "search", params={"query": query, "files": files, "folder": folders, "type": type, "extension": extension, "resultsLimit": max_results})
        return Folder._parse_children(None, data)

    def get_trash(self) -> Union[List[Union[Folder, File]], None]:
        data = make_request("GET", "trash")
        data = data['trash']
        return Folder._parse_children(None, data)

    def get_file(self, file_id) -> File:
        file = File(file_id)
        file._fetch_data()
        return file

    def get_folder(self, folder_id) -> Folder:
        folder = Folder(folder_id)
        folder._fetch_data()
        return folder

    def set_download_path(self, path: str):
        APIConfig.default_path = path

    def move_to_trash(self, items: List[Item]):
        common.move_to_trash(items)

    def restore_from_trash(self, items: List[Item]):
        common.restore_from_trash(items)

    def delete(self, items: List[Item]):
        common.delete(items)

    def move(self, items: List[Item], new_parent: Folder):
        common.move(items, new_parent)

    def download(self, items: List[Item], callback=None):
        download_url = common.get_zip_download_url(items)
        common.download_from_url(download_url)
