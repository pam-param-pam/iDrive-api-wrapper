import logging
from typing import Union, List

from .Config import APIConfig
from .models.DiscordSettings import DiscordSettings
from .models.File import File
from .models.Folder import Folder
from .models.Item import Item
from .models.ItemsList import ItemsList
from .models.Share import Share
from .models.UserProfile import UserProfile
from .utils import common
from .utils.UltraDownloader import UltraDownloader
from .utils.Uploader import Uploader
from .utils.WebsocketManager import WebsocketManager
from .utils.networker import make_request

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
        APIConfig.token = token
        self._ultraDownloader = None
        self.uploader = Uploader()
        self.websocket = WebsocketManager(self._token)

    @staticmethod
    def login(username: str, password: str) -> str:
        # todo leaking token if already logged in + another login
        data = make_request("POST", "auth/token/login", data={'username': username, 'password': password})
        return data['auth_token']

    def logout(self):
        pass

    def get_root(self):
        return Folder(self.get_user_profile().user.root)

    def search(self, query: str, files: bool = True, folders: bool = True, type: str = "", extension: str = "", max_results: int = 50) -> ItemsList:
        data = make_request("GET", "search", params={"query": query, "files": files, "folder": folders, "type": type, "extension": extension, "resultsLimit": max_results})
        return Folder._parse_children(None, data)

    def get_trash(self) -> Union[List[Union[Folder, File]], None]:
        data = make_request("GET", "trash")
        data = data['trash']
        return Folder._parse_children(None, data)

    def get_file(self, file_id, password=None) -> File:
        file = File(file_id)
        file.set_password(password)
        file._fetch_data()
        return file

    def get_folder(self, folder_id, password=None) -> Folder:
        folder = Folder(folder_id)
        folder.set_password(password)
        folder._fetch_data()
        return folder

    def set_download_path(self, path: str) -> None:
        APIConfig.default_path = path

    def move_to_trash(self, items: List[Item]) -> None:
        common.move_to_trash(items)

    def restore_from_trash(self, items: List[Item]) -> None:
        common.restore_from_trash(items)

    def delete(self, items: List[Item]) -> None:
        common.delete(items)

    def move(self, items: List[Item], new_parent: Folder) -> None:
        common.move(items, new_parent)

    def download(self, items: List[Item], callback=None) -> str:
        download_url = common.get_zip_download_url(items)
        return common.download_from_url(download_url)

    def get_share(self, token) -> Share:
        return Share(token)

    def get_shares(self) -> List[Share]:
        data = make_request("GET", "shares")
        shares = []
        for share_dict in data:
            share = Share(share_dict['token'])
            share._set_data(share_dict)
            shares.append(share)
        return shares

    def create_share(self) -> Share:
        data = make_request("GET", "shares")

    def get_user_profile(self) -> UserProfile:
        return UserProfile.fetch()

    def get_discord_settings(self) -> DiscordSettings:
        return DiscordSettings.fetch()

    def get_ultra_downloader(self, max_workers: int = 60) -> UltraDownloader:
        if not self._ultraDownloader:
            discord_settings = self.get_discord_settings()
            self._ultraDownloader = UltraDownloader(workers=min(3 * len(discord_settings.bots), max_workers))

        return self._ultraDownloader

    def set_debug_level(self, level):
        logger.setLevel(level)
