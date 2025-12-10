import os
from queue import Queue
from typing import Tuple, Dict

from .state import FileState, FragmentTask, FileInfo, FragmentInfo, FileRecord
from ..Config import APIConfig


class TaskPlanner:
    def prepare(self, files: list[FileInfo]) -> Tuple[
        Queue[FragmentTask],
        Queue[str],
        Dict[str, FileState],
        Dict[str, FileRecord],
        int
    ]:
        download_queue = Queue()
        finalize_queue = Queue()
        file_states = {}
        file_records = {}
        size_est = 0

        for file in files:
            file_id = file.id
            name = file.name
            fragments = file.fragments

            dir_ = os.path.join(APIConfig.download_folder, file_id)
            os.makedirs(dir_, exist_ok=True)
            merged = os.path.join(dir_, f"{name}.encrypted")
            out = os.path.join(dir_, name)

            missing, downloaded, est = self._missing(dir_, fragments)
            size_est += est

            file_states[file_id] = FileState(
                fragments_total=len(fragments),
                fragments_downloaded=downloaded,
            )

            file_records[file_id] = FileRecord(
                file_info=file,
                file_dir=dir_,
                merged_path=merged,
                output_path=out,
            )

            if downloaded == len(fragments):
                finalize_queue.put(file_id)
            else:
                for fragment in missing:
                    download_queue.put(FragmentTask(file_id=file_id, file_name=name, fragment=fragment, file_password=file.password))

        return download_queue, finalize_queue, file_states, file_records, size_est

    def _missing(self, dir_, fragments: list[FragmentInfo]) -> tuple[list, int, int]:
        missing = []
        downloaded = 0
        est = 0
        for frag in fragments:
            seq = frag.sequence
            part = os.path.join(dir_, f"{seq}.part")
            if os.path.exists(part):
                downloaded += 1
            else:
                missing.append(frag)
                est += frag.size
        return missing, downloaded, est
