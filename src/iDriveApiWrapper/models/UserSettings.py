from src.iDriveApiWrapper.utils.networker import make_request

#todo
class Settings:
    def __init__(self, locale: str, hideLockedFolders: bool, dateFormat, theme: str,
                 viewMode: str, sortingBy: str, sortByAsc: bool, subfoldersInShares: bool,
                 concurrentUploadRequests: int, encryptionMethod: int,
                 keepCreationTimestamp: bool):
        self.locale = locale
        self.hideLockedFolders = hideLockedFolders
        self.dateFormat = dateFormat
        self.theme = theme
        self.viewMode = viewMode
        self.sortingBy = sortingBy
        self.sortByAsc = sortByAsc
        self.subfoldersInShares = subfoldersInShares
        self.concurrentUploadRequests = concurrentUploadRequests
        self.encryptionMethod = encryptionMethod
        self.keepCreationTimestamp = keepCreationTimestamp

    _field_map = {
        "locale": "locale",
        "hide_locked_folders": "hideLockedFolders",
        "date_format": "dateFormat",
        "theme": "theme",
        "view_mode": "viewMode",
        "sorting_by": "sortingBy",
        "sort_by_asc": "sortByAsc",
        "subfolders_in_shares": "subfoldersInShares",
        "concurrent_upload_requests": "concurrentUploadRequests",
        "encryption_method": "encryptionMethod",
        "keep_creation_timestamp": "keepCreationTimestamp",
    }

    def to_api_dict(self):
        # Return dict with camelCase keys for API saving
        return {api_key: getattr(self, snake_attr) for snake_attr, api_key in self._field_map.items()}

    def save(self):
        data_to_save = self.to_api_dict()
        data = make_request("PATCH", "user/settings")
        # todo



