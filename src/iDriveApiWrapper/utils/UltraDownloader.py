import base64
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, List

import requests
from tqdm import tqdm

from .Decryptor import Decryptor
from .networker import make_request
from ..Config import APIConfig
from ..models.Enums import EncryptionMethod
from ..models.File import File
from ..models.Folder import Folder

logger = logging.getLogger("iDrive")


class UltraDownloader:
    def __init__(self, workers: int = 1):
        os.makedirs(APIConfig.download_folder, exist_ok=True)
        self.lock = threading.Lock()
        self.workers = workers

    def download(self, for_download: Union[File, Folder, List[Union[File, Folder]]], password: str = None):
        ids = [for_download.id]
        self._handle_download(ids, password)

    def _handle_download(self, ids: List[str], password: str = None):
        files = self._fetch_metadata(ids, password)
        for file in files:
            self.process_file(file)

    def download_from_ids(self, ids: List[str], password: str = None):
        pass

    def _fetch_metadata(self, ids: List[str] = None, password: str = None):
        response_data = make_request('POST', "items/ultraDownload", data={'ids': ids})
        return response_data

    def download_fragment(self, fragment, file_dir):
        attachment_id = fragment["attachment_id"]
        response_data = make_request('GET', f"items/ultraDownload/{attachment_id}")
        url = response_data['url']
        sequence = fragment["sequence"]
        filepath = os.path.join(file_dir, f"{sequence}.part")

        r = requests.get(url, stream=True)  # todo

        r.raise_for_status()

        total_bytes = 0
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

        return total_bytes

    def download_all_fragments(self, fragments, file_dir):
        total_size_estimate = sum([fragment.get("size", 0) for fragment in fragments])
        progress = tqdm(
            total=total_size_estimate or None,
            desc="Downloading",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            dynamic_ncols=True,
        )

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.download_fragment, f, file_dir): f for f in fragments}
            for future in as_completed(futures):
                try:
                    downloaded_bytes = future.result()
                    with self.lock:
                        progress.update(downloaded_bytes)
                except Exception as e:
                    logger.error(f"Error downloading fragment: {e}")

        progress.close()

    def merge_fragments(self, file_dir, output_path, total_fragments):
        with open(output_path, "wb") as output_file:
            for i in range(total_fragments):
                part_path = os.path.join(file_dir, f"{i + 1}.part")
                with open(part_path, "rb") as part_file:
                    output_file.write(part_file.read())

        # Remove fragment files after merging
        for i in range(total_fragments):
            part_path = os.path.join(file_dir, f"{i + 1}.part")
            os.remove(part_path)

    def decrypt_file(self, input_path, output_path, key: bytes, iv: bytes, method: EncryptionMethod):
        decryptor = Decryptor(method=method, key=key, iv=iv)

        with open(input_path, "rb") as encrypted_file, open(output_path, "wb") as decrypted_file:
            while True:
                chunk = encrypted_file.read(8192)
                if not chunk:
                    break
                decrypted_chunk = decryptor.decrypt(chunk)
                decrypted_file.write(decrypted_chunk)

            final_chunk = decryptor.finalize()
            if final_chunk:
                decrypted_file.write(final_chunk)

        # Remove the encrypted file after decryption
        os.remove(input_path)

    def process_file(self, file_info):
        file_name = file_info["name"]
        encryption_method = EncryptionMethod(file_info["encryption_method"])
        key = None
        iv = None
        if not encryption_method == EncryptionMethod.Not_Encrypted:
            key = base64.b64decode(file_info["key"])
            iv = base64.b64decode(file_info["iv"])

        fragments = file_info["fragments"]

        file_id = file_info["id"]
        file_dir = os.path.join(APIConfig.download_folder, file_id)
        os.makedirs(file_dir, exist_ok=True)

        merged_path = os.path.join(file_dir, f"{file_name}.encrypted")
        output_path = os.path.join(file_dir, f"{file_name}")

        print(f"\nProcessing: {file_name} ({len(fragments)} fragments)")

        # Skip everything if fully decrypted file exists
        if os.path.exists(output_path):
            print(f"✅ Already decrypted: {output_path}")
            return

        # Skip download if all part files exist
        missing_fragments = []
        for fragment in fragments:
            sequence = fragment["sequence"]
            part_path = os.path.join(file_dir, f"{sequence}.part")
            if not os.path.exists(part_path):
                missing_fragments.append(fragment)

        if missing_fragments:
            print(f"🔄 Resuming download, {len(missing_fragments)} missing fragments...")
            self.download_all_fragments(missing_fragments, file_dir)
        else:
            print(f"📁 All fragments already downloaded, skipping download.")

        # Merge only if merged file doesn't exist
        if not os.path.exists(merged_path):
            self.merge_fragments(file_dir, merged_path, len(fragments))
        else:
            print(f"📦 Encrypted file already merged: {merged_path}")

        self.decrypt_file(merged_path, output_path, key, iv, encryption_method)
        print(f"✅ Saved decrypted file to: {output_path}")