from src.iDriveApiWrapper.models.Enums import EncryptionMethod
from src.iDriveApiWrapper.utils.StreamCipherBase import StreamCipherBase


class Encryptor(StreamCipherBase):
    def _create_ctx(self, cipher):
        return cipher.encryptor()

    def encrypt(self, raw_data):
        if self.method == EncryptionMethod.Not_Encrypted:
            return raw_data
        return self._ctx.update(raw_data)
