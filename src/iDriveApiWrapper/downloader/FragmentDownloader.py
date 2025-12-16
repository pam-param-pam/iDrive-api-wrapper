import logging
import os
import time
import threading
import httpx

from .state import FragmentTask, FileRecord, FileState
from ..exceptions import RateLimitError, ServiceUnavailableError, DiscordAttachmentNotFoundError, ServerTimeoutError, NetworkError

from ..utils.networker import make_request

logger = logging.getLogger("iDrive")

class FragmentDownloader:
    def __init__(self):
        self._client = httpx.Client(timeout=10.0, follow_redirects=True)

    def download(self, task: FragmentTask, record: FileRecord, global_pause: threading.Event, state: FileState) -> int:
        if state.cancelled:
            return 0

        fragment = task.fragment
        attachment_id = fragment.attachment_id
        file_dir = record.file_dir
        part_path = os.path.join(file_dir, f"{fragment.sequence}.part")

        try:
            response_data = make_request("GET", f"items/ultraDownload/attachments/{attachment_id}", headers={"x-resource-password": task.file_password})
            url = response_data["url"]

            total = 0

            with self._client.stream("GET", url) as r:
                if r.status_code == 404:
                    raise DiscordAttachmentNotFoundError(f"Attachment {attachment_id} not found")

                if r.status_code == 429:
                    raise RateLimitError(r)

                if r.status_code == 503:
                    raise ServiceUnavailableError(r)

                r.raise_for_status()

                with open(part_path, "wb") as f:
                    for chunk in r.iter_bytes(8192):
                        if not chunk:
                            continue

                        # pause / cancel
                        while not global_pause.is_set() or not state.pause_event.is_set():
                            if state.cancelled:
                                return total
                            time.sleep(0.1)

                        if state.cancelled:
                            return total

                        f.write(chunk)
                        total += len(chunk)

            return total

        except (httpx.TimeoutException, httpx.ReadTimeout) as e:
            self._cleanup_file(part_path)
            raise ServerTimeoutError("Download timed out") from e
        except httpx.RequestError as e:
            self._cleanup_file(part_path)
            raise NetworkError("Network error during download") from e

    def _cleanup_file(self, path: str) -> None:
        logger.info("[FragmentDownloader] Cleaning up file after network error")
        if os.path.exists(path):
            os.remove(path)
