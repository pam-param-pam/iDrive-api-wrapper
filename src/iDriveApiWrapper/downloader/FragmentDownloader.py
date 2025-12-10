# downloader/fragment_downloader.py
import os
import requests

from .state import FragmentTask, FileRecord
from ..exceptions import RateLimitError, ServiceUnavailableError
from ..utils.networker import make_request


class FragmentDownloader:

    def download(self, task: FragmentTask, record: FileRecord):
        fragment = task.fragment
        file_dir = record.file_dir
        attachment_id = fragment.attachment_id

        # Signed URL fetch
        response_data = make_request("GET", f"items/ultraDownload/{attachment_id}", headers={"x-resource-password": task.file_password})
        url = response_data["url"]

        r = requests.get(url, stream=True, timeout=30)

        if r.status_code == 404:
            raise FileNotFoundError(f"Attachment {attachment_id} not found")

        if r.status_code == 429:
            raise RateLimitError(r)
        if r.status_code == 503:
            raise ServiceUnavailableError(r)

        r.raise_for_status()

        filepath = os.path.join(file_dir, f"{fragment.sequence}.part")

        total = 0
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)

        return total

    @staticmethod
    def _parse_retry(response) -> float:
        return 2.0

        retry_after = response.headers.get("Retry-After")
        try:
            print("float(retry_after)")
            print(float(retry_after))
            return float(retry_after)
        except:
            print("_parse_retry fallback")
            return 2.0
