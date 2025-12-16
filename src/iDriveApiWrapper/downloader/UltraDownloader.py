import os
import tempfile
import threading
from queue import Queue, Empty
from typing import Dict, List, Optional

from .AutoScaler import AutoScaler
from .DownloadWorker import DownloadWorker
from .FinalizeWorker import FinalizeWorker
from .MetadataFetcher import MetadataFetcher
from .TaskPlanner import TaskPlanner
from .state import (
    ThrottleState,
    FragmentTask,
    FileState,
    FileRecord,
    FileStatus, onCompleteCallback,
)
from ..Config import APIConfig
from ..models.Item import Item


class UltraDownloader:
    def __init__(self, max_workers: int):
        self._temp_download_folder = os.path.join(tempfile.gettempdir(), "idrive_download")
        os.makedirs(self._temp_download_folder, exist_ok=True)

        self.metadata_fetcher = MetadataFetcher()
        self.planner = TaskPlanner(self._temp_download_folder)

        self.throttle = ThrottleState()
        self.scaler = AutoScaler(max_workers=max_workers, throttle_state=self.throttle)

        self.max_retries = 5
        self.post_workers = 2

        # Persistent queues
        self._fragment_queue: Queue[FragmentTask] = Queue()
        self._finalize_queue: Queue[str] = Queue()

        # Shared state
        self._states: Dict[str, FileState] = {}
        self._records: Dict[str, FileRecord] = {}

        self._global_pause = threading.Event()
        self._global_pause.set()

        self._lock = threading.RLock()
        self._last_error: Optional[Exception] = None

        self._download_threads: List[threading.Thread] = []
        self._finalize_threads: List[threading.Thread] = []

        self._start_workers()

    def _guard_new_file_ids(self, new_states: Dict[str, FileState]) -> None:
        duplicates = set(new_states.keys()) & set(self._states.keys())
        if duplicates:
            raise RuntimeError(f"Attempted to enqueue already-existing file_ids: {sorted(duplicates)}")

    # ------------------------------------------------------------------
    # Worker startup (ONCE)
    # ------------------------------------------------------------------

    def _start_workers(self) -> None:
        def spawn_one():
            t = self._start_download_thread()
            self._download_threads.append(t)

        def kill_one():
            self._fragment_queue.put(None)

        # Spawn minimum workers
        for _ in range(self.scaler.min):
            spawn_one()

        # Start autoscaler
        self.scaler.start(spawn_one, kill_one)

        # Start finalize workers
        for _ in range(self.post_workers):
            t = self._start_finalize_thread()
            self._finalize_threads.append(t)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(self, data: Item, target_dir: str = APIConfig.download_folder, on_complete: onCompleteCallback = None) -> None:
        files = self.metadata_fetcher.fetch_files(data)

        plan_queue, finalize_queue, states, records, size_est = self.planner.prepare(files, target_dir, on_complete)

        with self._lock:
            self._guard_new_file_ids(states)

            for fid, st in states.items():
                self._states[fid] = st

            for fid, rec in records.items():
                self._records[fid] = rec

        # enqueue finalize tasks (already completed files)
        while True:
            try:
                file_id = finalize_queue.get_nowait()
            except Empty:
                break
            self._finalize_queue.put(file_id)

        # enqueue fragment tasks
        while True:
            try:
                task = plan_queue.get_nowait()
            except Empty:
                break
            self._fragment_queue.put(task)

    # ------------------------------------------------------------------
    # State querying
    # ------------------------------------------------------------------

    def get_file_state(self, file_id: str) -> FileState:
        return self._states[file_id]

    def get_all_states(self) -> Dict[str, FileState]:
        return dict(self._states)

    def get_failed_states(self) -> Dict[str, FileState]:
        return {fid: st for fid, st in self._states.items() if st.error}

    def get_download_rate(self) -> float:
        return self.throttle.download_rate()

    def get_last_error(self) -> Optional[Exception]:
        return self._last_error

    # ------------------------------------------------------------------
    # Global pause / resume
    # ------------------------------------------------------------------

    def pause_all(self) -> None:
        self._global_pause.clear()
        for st in self._states.values():
            with st.lock:
                if st.status == FileStatus.DOWNLOADING:
                    st.status = FileStatus.PAUSED

    def resume_all(self) -> None:
        self._global_pause.set()
        for st in self._states.values():
            with st.lock:
                if st.status == FileStatus.PAUSED and not st.cancelled:
                    st.status = FileStatus.DOWNLOADING

    # ------------------------------------------------------------------
    # Per-file control
    # ------------------------------------------------------------------

    def pause_file(self, file_id: str) -> None:
        st = self._states[file_id]
        with st.lock:
            st.pause_event.clear()
            if st.status == FileStatus.DOWNLOADING:
                st.status = FileStatus.PAUSED

    def resume_file(self, file_id: str) -> None:
        st = self._states[file_id]
        with st.lock:
            st.pause_event.set()
            if (
                st.status == FileStatus.PAUSED
                and not st.cancelled
                and st.error is None
                and st.fragments_downloaded < st.fragments_total
            ):
                st.status = FileStatus.DOWNLOADING

    def cancel_file(self, file_id: str) -> None:
        st = self._states[file_id]
        with st.lock:
            st.cancelled = True
            st.status = FileStatus.CANCELLED

    # ------------------------------------------------------------------
    # Worker helpers
    # ------------------------------------------------------------------

    def _start_download_thread(self) -> threading.Thread:
        worker = DownloadWorker(
            self._fragment_queue,
            self._finalize_queue,
            self._states,
            self._records,
            self.max_retries,
            self.throttle,
            self._global_pause,
        )
        t = threading.Thread(target=worker.run, daemon=True)
        t.start()
        return t

    def _start_finalize_thread(self) -> threading.Thread:
        worker = FinalizeWorker(self._finalize_queue, self._states, self._records)
        t = threading.Thread(target=worker.run, daemon=True)
        t.start()
        return t

    # ------------------------------------------------------------------
    # Optional: graceful shutdown
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        for _ in self._download_threads:
            self._fragment_queue.put(None)
        for t in self._download_threads:
            t.join()

        for _ in self._finalize_threads:
            self._finalize_queue.put(None)
        for t in self._finalize_threads:
            t.join()

        self.scaler.stop()
