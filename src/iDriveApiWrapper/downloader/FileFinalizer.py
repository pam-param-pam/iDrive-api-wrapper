import os
import base64
import zlib

from .state import FileRecord, FileInfo
from ..models.Enums import EncryptionMethod
from ..utils.Decryptor import Decryptor


class FileFinalizer:

    def finalize(self, record: FileRecord):
        file_info = record.file_info
        file_dir = record.file_dir
        merged_path = record.merged_path
        output_path = record.output_path

        fragments = file_info.fragments

        if not os.path.exists(merged_path):
            self._merge_fragments(file_dir, merged_path, len(fragments))

        self._decrypt(file_info, merged_path, output_path)

        self._verify_crc(output_path, file_info.crc)

        self._remove_fragments(file_dir, len(fragments))

    def _merge_fragments(self, file_dir, merged_path, count):
        with open(merged_path, "wb") as out:
            for i in range(1, count + 1):
                path = os.path.join(file_dir, f"{i}.part")
                with open(path, "rb") as p:
                    out.write(p.read())

    def _decrypt(self, info: FileInfo, inp, outp):
        method = EncryptionMethod(info.encryption_method)
        if method == EncryptionMethod.Not_Encrypted:
            os.rename(inp, outp)
            return

        key = base64.b64decode(info.key)
        iv = base64.b64decode(info.iv)
        dec = Decryptor(method, key, iv)

        with open(inp, "rb") as i, open(outp, "wb") as o:
            for chunk in iter(lambda: i.read(8192), b""):
                o.write(dec.decrypt(chunk))
            final = dec.finalize()
            if final:
                o.write(final)

        os.remove(inp)

    def _verify_crc(self, path, expected):
        crc = 0
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                crc = zlib.crc32(chunk, crc)
        if (crc & 0xFFFFFFFF) != expected:
            raise ValueError("CRC mismatch")

    def _remove_fragments(self, file_dir, count):
        for i in range(1, count + 1):
            p = os.path.join(file_dir, f"{i}.part")
            if os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass
