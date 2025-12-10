import logging

from src.iDriveApiWrapper.downloader.FileFinalizer import FileFinalizer

logger = logging.getLogger("iDrive")


class FinalizeWorker:
    def __init__(self, finalize_q, file_states, file_records):
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

            if state.error is None:
                try:
                    self.finalizer.finalize(record)
                except Exception as e:
                    state.error = e

            self.fq.task_done()
