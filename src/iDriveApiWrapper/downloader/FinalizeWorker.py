import logging
import os
import shutil
from typing import Dict

from src.iDriveApiWrapper.downloader.FileFinalizer import FileFinalizer
from .state import FileStatus, FileRecord, FileState
from ..exceptions import PathDoesntExistError

logger = logging.getLogger("iDrive")

# Cleaned v.1

class FinalizeWorker:
    def __init__(self, finalize_q, file_states: Dict[str, FileState], file_records: Dict[str, FileRecord]):
        self.fq = finalize_q
        self.file_states = file_states
        self.file_records = file_records
        self.finalizer = FileFinalizer()

    def run(self):
        while True:
            fid = self.fq.get()
            if fid is None:
                self.fq.task_done()
                break

            state = self.file_states[fid]
            record = self.file_records[fid]

            try:
                if state.cancelled:
                    state.status = FileStatus.CANCELLED

                elif state.error is None:
                    self.finalizer.finalize(record)

                    output_dir = record.output_dir

                    if not os.path.isdir(output_dir):
                        raise PathDoesntExistError(f"Target directory does not exist: {output_dir}")

                    target_path = os.path.join(output_dir, os.path.basename(record.output_path))
                    shutil.move(record.output_path, target_path)
                    shutil.rmtree(record.file_dir)

                    state.status = FileStatus.COMPLETED

                else:
                    state.status = FileStatus.FAILED

            except Exception as e:
                state.error = e
                state.status = FileStatus.FAILED
                logger.exception(f"[FinalizeWorker] Finalization failed for file {fid}")

            finally:
                try:
                    if record.on_complete:
                        record.on_complete(fid, state)
                except Exception:
                    logger.exception(f"[FinalizeWorker] on_complete callback failed for file {fid}")

                self.fq.task_done()
