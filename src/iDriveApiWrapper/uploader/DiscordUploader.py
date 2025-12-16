import logging
import time
import httpx

from .state import DiscordRequest
from ..exceptions import RateLimitError, ServiceUnavailableError, ServerTimeoutError, NetworkError

logger = logging.getLogger("iDrive")

#todo unchecked

class DiscordUploader:
    def __init__(self, get_config, global_pause, states):
        self._get_config = get_config
        self._client = httpx.Client(timeout=10.0, follow_redirects=True)
        self.global_pause = global_pause
        self.states = states

    @property
    def config(self):
        return self._get_config()

    def upload(self, request: DiscordRequest) -> None:
        # states: file_id -> UploadFileState (all files affected by this request)

        # early cancel
        for st in self.states.values():
            if st.cancelled:
                return

        webhook = self._pick_webhook()
        url = webhook.url

        try:
            files = {}
            payload = {}

            # pause before starting network I/O
            while not self.global_pause.is_set() or not self._all_unpaused(self.states):
                if self._any_cancelled(self.states):
                    return
                time.sleep(0.1)

            for idx, att in enumerate(request.attachments):
                files[f"files[{idx}]"] = (
                    self._attachment_name(att),
                    att.data,
                    "application/octet-stream",
                )

            response = self._client.post(url, data=payload, files=files)

            if response.status_code == 429:
                raise RateLimitError(response)

            if response.status_code == 503:
                raise ServiceUnavailableError(response)

            response.raise_for_status()

        except (httpx.TimeoutException, httpx.ReadTimeout) as e:
            raise ServerTimeoutError("Upload timed out") from e
        except httpx.RequestError as e:
            raise NetworkError("Network error during upload") from e

    def _pick_webhook(self):
        # naive round-robin or first; improve later if needed
        return self.config.webhooks[0]

    def _attachment_name(self, att) -> str:
        base = self.config.attachment_name
        return f"{base}_{att.frontend_id.hex}"

    def _all_unpaused(self, states: dict) -> bool:
        for st in states.values():
            if not st.pause_event.is_set():
                return False
        return True

    def _any_cancelled(self, states: dict) -> bool:
        for st in states.values():
            if st.cancelled:
                return True
        return False
