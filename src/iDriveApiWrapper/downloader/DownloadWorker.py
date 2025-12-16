import logging
import time
import threading
from typing import Dict
from queue import Queue

from .FragmentDownloader import FragmentDownloader
from .state import ThrottleState, FileRecord, FileState, FragmentTask, FileStatus
from ..exceptions import RateLimitError, ServiceUnavailableError, NetworkError, ServerTimeoutError

logger = logging.getLogger("iDrive")


class DownloadWorker:
    def __init__(self, fragment_queue: Queue[FragmentTask], finalize_queue: Queue[str], file_states: Dict[str, FileState],
                 file_records: Dict[str, FileRecord], max_retries: int, throttle: ThrottleState, global_pause: threading.Event) -> None:
        self.fragment_queue = fragment_queue
        self.finalize_queue = finalize_queue
        self.file_states = file_states
        self.file_records = file_records
        self.max_retries = max_retries
        self.throttle = throttle
        self.global_pause = global_pause
        self.http = FragmentDownloader()

    def run(self) -> None:
        while True:
            task = self.fragment_queue.get()

            if task is None:
                self.fragment_queue.task_done()
                break

            state = self.file_states.get(task.file_id)
            if state is None or state.cancelled:
                self.fragment_queue.task_done()
                continue

            if not self.global_pause.is_set() or not state.pause_event.is_set():
                self.fragment_queue.put(task)
                self.fragment_queue.task_done()
                time.sleep(0.05)
                continue

            try:
                with state.lock:
                    if state.status not in (FileStatus.COMPLETED, FileStatus.FAILED, FileStatus.CANCELLED):
                        state.status = FileStatus.DOWNLOADING

                bytes_downloaded = self._download_fragment(task)

                if isinstance(bytes_downloaded, int) and bytes_downloaded > 0:
                    with state.lock:
                        state.bytes_downloaded += bytes_downloaded

                with state.lock:
                    if not state.cancelled:
                        state.fragments_downloaded += 1
                        if state.fragments_downloaded == state.fragments_total:
                            self.finalize_queue.put(task.file_id)

            except (RateLimitError, ServiceUnavailableError) as e:
                self.throttle.signal_error()
                if task.retries >= self.max_retries:
                    with state.lock:
                        state.error = e
                        state.status = FileStatus.FAILED
                else:
                    logger.warning(f"[DownloadWorker] Throttled ({e.__class__.__name__}) → retrying in {e.wait}s (retry {task.retries})")
                    time.sleep(e.wait)
                    task.retries += 1
                    self.fragment_queue.put(task)

            except (NetworkError, ServerTimeoutError) as e:
                with state.lock:
                    state.status = FileStatus.RETRYING_NETWORK
                logger.warning(f"[DownloadWorker] Network issue ({e.__class__.__name__}) → waiting 5s")
                time.sleep(5)
                self.fragment_queue.put(task)

            except Exception as e:
                with state.lock:
                    state.error = e
                    state.status = FileStatus.FAILED
                logger.exception(f"[DownloadWorker] Unexpected failure for file {task.file_id}")

            finally:
                self.fragment_queue.task_done()

    def _download_fragment(self, task: FragmentTask) -> int:
        file_record = self.file_records[task.file_id]
        state = self.file_states[task.file_id]

        bytes_count = self.http.download(task, file_record, self.global_pause, state)
        self.throttle.signal_bytes(bytes_count)

        return bytes_count
