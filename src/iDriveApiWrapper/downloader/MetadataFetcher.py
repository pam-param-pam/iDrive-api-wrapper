import logging

from .state import FileInfo
from .typehints import DownloadInput
from ..utils.networker import make_request

logger = logging.getLogger("iDrive")


class MetadataFetcher:

    def _make_required_password(self, data: DownloadInput) -> dict:
        required_passwords = {}
        for item in data:
            lock_from_id = item.lock_from
            if lock_from_id not in required_passwords:
                required_passwords[lock_from_id] = item.get_password()
        return required_passwords

    def _make_file_password_lookup(self, data: DownloadInput) -> dict[str, str]:
        lookup = {}
        for item in data:
            lookup[item.id] = item.get_password()
        return lookup

    def _inject_passwords(self, raw_files: dict, file_passwords: dict[str, str]):
        for f in raw_files:
            f["password"] = file_passwords.get(f["id"])
        return raw_files

    def _make_ids(self, data) -> list[str]:
        return [item.id for item in data]

    def fetch_files(self, data: DownloadInput) -> list[FileInfo]:
        required_passwords = self._make_required_password(data)
        ids = self._make_ids(data)
        res_data = make_request("POST", "items/ultraDownload", data={"ids": ids, "required_passwords": required_passwords})

        file_passwords = self._make_file_password_lookup(data)
        res_data = self._inject_passwords(res_data, file_passwords)

        return FileInfo.convert(res_data)

