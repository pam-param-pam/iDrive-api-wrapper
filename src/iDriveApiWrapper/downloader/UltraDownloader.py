import threading
import traceback
from queue import Queue
from typing import Dict, List

from .AutoScaler import AutoScaler
from .DownloadWorker import DownloadWorker
from .FinalizeWorker import FinalizeWorker
from .MetadataFetcher import MetadataFetcher
from .TaskPlanner import TaskPlanner
from .state import ThrottleState, FragmentTask, FileState, FileRecord
from .typehints import DownloadInput
from .utils import create_progress_bar


class UltraDownloader:
    def __init__(self):
        self.metadata_fetcher = MetadataFetcher()
        self.planner = TaskPlanner()

        self.throttle = ThrottleState()
        self.scaler = AutoScaler(max_workers=80, throttle_state=self.throttle)
        self.post_workers = 2
        self.max_retries = 5

        self.active_download_threads = None

    def download(self, data: DownloadInput):
        if not isinstance(data, list):
            data = [data]

        # Fetch metadata
        files = self.metadata_fetcher.fetch_files(data)

        # Build queues, file states & records
        dq, fq, states, records, size_est = self.planner.prepare(files)
        progress = create_progress_bar(size_est)

        # ------------------------------
        # 1. Spawn minimal worker set
        # ------------------------------
        self.active_download_threads = []

        def spawn_one():
            t = self._start_download_thread(dq, fq, states, records, progress)
            self.active_download_threads.append(t)

        def kill_one():
            dq.put(None)  # Sentinel to kill one worker

        for _ in range(self.scaler.min):
            spawn_one()

        # ------------------------------
        # 2. Start scaler thread
        # ------------------------------
        scaler_thread = self.scaler.start(spawn_one, kill_one)

        # ------------------------------
        # 3. Wait for all download tasks to finish
        # ------------------------------
        dq.join()

        # ------------------------------
        # 4. Now tell scaler to stop
        # ------------------------------
        self.scaler.stop()
        scaler_thread.join()

        # ------------------------------
        # 5. Kill remaining workers cleanly
        # ------------------------------
        for _ in self.active_download_threads:
            dq.put(None)

        for t in self.active_download_threads:
            t.join()

        # ------------------------------
        # 6. Run finalizers
        # ------------------------------
        fthreads = [
            self._start_finalize_thread(fq, states, records)
            for _ in range(self.post_workers)
        ]

        fq.join()
        for _ in fthreads:
            fq.put(None)
        for t in fthreads:
            t.join()

        progress.close()
        self._check_errors(states)

    def _start_download_thread( self, dq: Queue[FragmentTask], fq: Queue[str], states: Dict[str, FileState], records: Dict[str, FileRecord], progress) -> threading.Thread:
        worker = DownloadWorker(dq, fq, states, records, progress, self.max_retries, self.throttle)
        t = threading.Thread(target=worker.run)
        t.start()
        return t

    def _start_finalize_thread(self, fq: Queue[str], states: Dict[str, FileState], records: Dict[str, FileRecord]) -> threading.Thread:
        worker = FinalizeWorker(fq, states, records)
        t = threading.Thread(target=worker.run)
        t.start()
        return t

    def _join_threads(self, dq: Queue[FragmentTask], fq: Queue[str], dthreads: List[threading.Thread], fthreads: List[threading.Thread]) -> None:
        dq.join()
        for _ in dthreads:
            dq.put(None)  # sentinel for each worker
        for t in dthreads:
            t.join()

        fq.join()
        for _ in fthreads:
            fq.put(None)
        for t in fthreads:
            t.join()

    def _check_errors(self, states: Dict[str, FileState]) -> None:
        errors = [st.error for st in states.values() if st.error]

        if not errors:
            return

        for err in errors:
            traceback.print_exception(type(err), err, err.__traceback__)

        # raise only the *first* error to stop execution
        raise RuntimeError(f"Errors occurred (see full traceback above): {errors[0]}")
