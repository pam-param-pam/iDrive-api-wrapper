import os
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Mapping, Literal

from src.iDriveApiWrapper.models.Enums import EncryptionMethod
from src.iDriveApiWrapper.models.Folder import Folder
from src.iDriveApiWrapper.models.VideoMetadata import VideoMetadata
from src.iDriveApiWrapper.models.Webhook import Webhook

"""Goofy class to change"""
@dataclass(frozen=True)
class UploadConfig:
    webhooks: list[Webhook]
    extensions: Mapping[str, list[str]]
    attachment_name: str
    max_attachments: int
    max_size: int
    encryption_method: EncryptionMethod


@dataclass(frozen=True)
class Crypto:
    method: EncryptionMethod
    key: Optional[bytes]
    iv: Optional[bytes]

    @staticmethod
    def generate(method: EncryptionMethod) -> "Crypto":
        if method == EncryptionMethod.Not_Encrypted:
            return Crypto(method=method, key=None, iv=None)

        if method == EncryptionMethod.AES_CTR:
            key = os.urandom(32)   # AES-256
            iv = os.urandom(16)    # 128-bit counter block
            return Crypto(method=method, key=key, iv=iv)

        if method == EncryptionMethod.CHA_CHA_20:
            key = os.urandom(32)   # ChaCha20 key
            iv = os.urandom(12)    # 96-bit nonce (RFC 8439)
            return Crypto(method=method, key=key, iv=iv)

        raise ValueError(f"Unsupported encryption method: {method}")


"""Upload input given to UltraUploader and passed to PrepareRequestWorker"""
@dataclass(frozen=True)
class UploadInput:
    path: Path
    parent: Folder
    lock_from_id: Optional[str]


"""Extracted thumbnail"""
@dataclass(frozen=True)
class ExtractedThumbnail:
    data: bytes


"""Extracted subtitle"""
@dataclass(frozen=True)
class ExtractedSubtitle:
    data: bytes
    language: str
    is_forced: bool


@dataclass(frozen=True)
class DiscordAttachment:
    frontend_id: uuid.UUID
    data: bytes
    crypto: Crypto

    @property
    def size(self) -> int:
        return len(self.data)


@dataclass(frozen=True)
class ChunkAttachment(DiscordAttachment):
    sequence: Optional[int] = None
    offset: Optional[int] = None

    def __str__(self):
        return f"ChunkAttachment[frontend_ig={self.frontend_id!r}, sequence={self.sequence!r}, offset={self.offset}]"

    __repr__ = __str__

@dataclass(frozen=True)
class ThumbnailAttachment(DiscordAttachment):
    def __str__(self):
        return f"ThumbnailAttachment[frontend_ig={self.frontend_id!r}]"

    __repr__ = __str__

@dataclass(frozen=True)
class SubtitleAttachment(DiscordAttachment):
    language: Optional[str] = None
    is_forced: Optional[bool] = None

    def __str__(self):
        return f"ChunkAttachment[frontend_ig={self.frontend_id!r}, language={self.language!r}, is_forced={self.is_forced}]"

    __repr__ = __str__

@dataclass(frozen=True)
class DiscordRequest:
    attachments: list[ChunkAttachment | ThumbnailAttachment | SubtitleAttachment | DiscordAttachment]
    request_id: uuid.UUID = uuid.uuid4()
    retries: int = 0

    @property
    def total_size(self):
        total_size = 0
        for attachment in self.attachments:
            total_size += attachment.size
        return total_size


class UploadFileStatus(Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    READY = "ready"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING_NETWORK = "retrying_network"

@dataclass
class UploadFileState:
    expected_chunks: int
    expected_subtitles: int
    expected_thumbnail: int
    uploaded_chunks: int = 0
    uploaded_subtitles: int = 0
    uploaded_thumbnail: int = 0
    status: UploadFileStatus = UploadFileStatus.PENDING
    error: Optional[Exception] = None
    cancelled: bool = False
    pause_event: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        # By default files are not paused
        self.pause_event.set()

    def is_fully_extracted(self) -> bool:
        return self.uploaded_chunks == self.expected_chunks and self.uploaded_subtitles == self.expected_subtitles and self.uploaded_thumbnail == self.expected_thumbnail

    def is_terminal(self) -> bool:
        return self.status in (UploadFileStatus.COMPLETED, UploadFileStatus.FAILED, UploadFileStatus.CANCELLED)

@dataclass
class UploadFileArtifacts:
    file_crypto: Crypto = None
    crc: int = 0
    video_metadata: Optional[VideoMetadata] = None
