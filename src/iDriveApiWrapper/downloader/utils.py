# downloader/progress.py
from tqdm import tqdm


def create_progress_bar(total_size: int):
    """
    Create a tqdm progress bar identical to the old inline one.
    If total_size is 0, tqdm uses an indeterminate (unknown total) bar.
    """
    return tqdm(
        total=total_size or None,
        desc="Downloading",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        dynamic_ncols=True,
    )
