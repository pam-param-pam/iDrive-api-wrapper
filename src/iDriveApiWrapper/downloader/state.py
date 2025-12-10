# downloader/state.py
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, List, Union


@dataclass
class FragmentInfo:
    message_id: str
    attachment_id: str
    offset: int
    sequence: int
    size: int


@dataclass
class FileInfo:
    id: str
    name: str
    encryption_method: int
    size: int
    crc: int
    password: Optional[str]
    key: Optional[str] = None
    iv: Optional[str] = None
    fragments: List[FragmentInfo] = field(default_factory=list)

    def __str__(self):
        return (
            f"FileInfo("
            f"id={self.id!r}, "
            f"name={self.name!r}, "
            f"fragments={len(self.fragments)})"
        )

    __repr__ = __str__

    @staticmethod
    def convert(data: Union[list, dict]) -> List['FileInfo']:
        result = []
        for item in data:
            fragments = [FragmentInfo(**frag) for frag in item["fragments"]]
            file_obj = FileInfo(
                id=item["id"],
                name=item["name"],
                encryption_method=item["encryption_method"],
                crc=item["crc"],
                size=item["size"],
                key=item.get("key"),
                iv=item.get("iv"),
                password=item["password"],
                fragments=fragments,
            )
            result.append(file_obj)
        return result


@dataclass
class FragmentTask:
    file_id: str
    file_name: str
    fragment: FragmentInfo
    file_password: Optional[str]
    retries: int = 0


@dataclass
class FileState:
    fragments_total: int
    fragments_downloaded: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)
    error: Optional[Exception] = None

@dataclass
class FileRecord:
    file_info: FileInfo
    file_dir: str
    merged_path: str
    output_path: str


class ThrottleState:
    def __init__(self, window: int = 10):
        self.lock = threading.Lock()
        self.window = window  # lookback window (seconds)

        # soft retryable errors (e.g. connection reset, timeouts, etc.)
        self._retry_events = []       # [timestamp]

        # hard throttling (429, 503, etc.)
        self._hard_events = []        # [timestamp]

        # download throughput
        self._byte_events = []        # [(timestamp, bytes)]

    # ---------------------------
    # soft retries
    # ---------------------------

    def signal_retry(self) -> None:
        now = time.time()
        with self.lock:
            self._retry_events.append(now)
            self._prune_times(self._retry_events, now)

    def retry_rate(self) -> int:
        """How many soft retry events in last window."""
        now = time.time()
        with self.lock:
            self._prune_times(self._retry_events, now)
            return len(self._retry_events)

    # ---------------------------
    # hard errors (429 / 503)
    # ---------------------------

    def signal_hard_error(self) -> None:
        now = time.time()
        with self.lock:
            self._hard_events.append(now)
            self._prune_times(self._hard_events, now)

    def hard_error_rate(self) -> int:
        """How many hard throttling events in last window."""
        now = time.time()
        with self.lock:
            self._prune_times(self._hard_events, now)
            return len(self._hard_events)

    # ---------------------------
    # throughput
    # ---------------------------

    def signal_bytes(self, byte_count: int) -> None:
        """Record bytes downloaded by *any* worker."""
        if byte_count <= 0:
            return
        now = time.time()
        with self.lock:
            self._byte_events.append((now, byte_count))
            self._prune_bytes(now)

    def download_rate(self) -> float:
        """
        Bytes/sec averaged over the window.
        """
        now = time.time()
        with self.lock:
            self._prune_bytes(now)
            if not self._byte_events:
                return 0.0

            total_bytes = sum(b for _, b in self._byte_events)
            first_ts = self._byte_events[0][0]
            duration = max(now - first_ts, 0.001)
            return total_bytes / duration

    # ---------------------------
    # helpers
    # ---------------------------

    def _prune_times(self, arr, now: float) -> None:
        cutoff = now - self.window
        # drop from the front while older than cutoff
        i = 0
        for t in arr:
            if t >= cutoff:
                break
            i += 1
        if i:
            del arr[:i]

    def _prune_bytes(self, now: float) -> None:
        cutoff = now - self.window
        self._byte_events = [(t, b) for (t, b) in self._byte_events if t >= cutoff]
