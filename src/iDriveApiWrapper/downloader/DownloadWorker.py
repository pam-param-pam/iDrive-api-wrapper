import logging
import time
from typing import Dict
from queue import Queue

from .FragmentDownloader import FragmentDownloader
from .state import ThrottleState, FileRecord, FileState, FragmentTask
from ..exceptions import RateLimitError, ServiceUnavailableError

logger = logging.getLogger("iDrive")


class DownloadWorker:
    def __init__(
        self,
        dq: Queue[FragmentTask],
        fq: Queue[str],
        file_states: Dict[str, FileState],
        file_records: Dict[str, FileRecord],
        progress,
        max_retries: int,
        throttle: ThrottleState,
    ) -> None:
        self.throttle = throttle
        self.dq = dq
        self.fq = fq
        self.file_states = file_states
        self.file_records = file_records
        self.progress = progress
        self.max_retries = max_retries
        self.http = FragmentDownloader()

    def run(self):
        while True:
            task = self.dq.get()
            if task is None:  # sentinel → exit
                self.dq.task_done()
                break

            try:
                bytes_downloaded = self._download_fragment(task)

                # Update progress bar
                if bytes_downloaded > 0:
                    self.progress.update(bytes_downloaded)

                # Mark fragment complete
                st = self.file_states[task.file_id]
                with st.lock:
                    st.fragments_downloaded += 1
                    if st.fragments_downloaded == st.fragments_total:
                        self.fq.put(task.file_id)

            except (RateLimitError, ServiceUnavailableError) as e:
                # HARD ERROR → tell autoscaler
                self.throttle.signal_hard_error()

                wait = e.wait if e.wait is not None else 1  # safe fallback

                if task.retries >= self.max_retries:
                    self.file_states[task.file_id].error = e
                else:
                    logger.warning(
                        f"[DownloadWorker] Hard throttling ({e.__class__.__name__}) "
                        f"→ retrying in {wait}s (retry {task.retries})"
                    )

                    time.sleep(wait)
                    task.retries += 1
                    self.dq.put(task)

            except Exception as e:
                # OTHER RETRYABLE ERROR
                self.throttle.signal_retry()

                if task.retries >= self.max_retries:
                    self.file_states[task.file_id].error = e
                else:
                    logger.warning(
                        f"[DownloadWorker] Soft error {e.__class__.__name__} → retry {task.retries}"
                    )
                    task.retries += 1
                    self.dq.put(task)

            finally:
                self.dq.task_done()

    # ----------------------------------------
    # Internal: perform the fragment download
    # and emit throttle signals
    # ----------------------------------------
    def _download_fragment(self, task: FragmentTask) -> int:
        file_rec = self.file_records[task.file_id]

        # Download whole fragment (your current API)
        bytes_count = self.http.download(task, file_rec)

        # Tell autoscaler how busy we are
        if isinstance(bytes_count, int) and bytes_count > 0:
            self.throttle.signal_bytes(bytes_count)

        return bytes_count
