import time

from tqdm import tqdm

from src.iDriveApiWrapper.downloader.UltraDownloader import UltraDownloader
from src.iDriveApiWrapper.downloader.state import FileStatus


def watch_file_download(downloader: UltraDownloader, file_id: str, poll_interval: float = 0.2) -> None:
    state = downloader.get_file_state(file_id)

    total = state.size_total
    initial = state.bytes_downloaded

    with tqdm(
        total=total,
        initial=initial,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=f"Downloading {file_id}",
    ) as bar:

        last_bytes = initial

        while True:
            downloaded = state.bytes_downloaded
            delta = downloaded - last_bytes
            if delta > 0:
                bar.update(delta)
                last_bytes = downloaded

            if state.status in (
                FileStatus.COMPLETED,
                FileStatus.FAILED,
                FileStatus.CANCELLED,
            ):
                break

            time.sleep(poll_interval)

    if state.status == FileStatus.FAILED:
        raise RuntimeError(f"Download failed for file {file_id}: {state.error}")

    if state.status == FileStatus.CANCELLED:
        raise RuntimeError(f"Download cancelled for file {file_id}")
