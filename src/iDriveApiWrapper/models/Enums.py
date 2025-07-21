from enum import Enum


class EncryptionMethod(Enum):
    Not_Encrypted = 0
    AES_CTR = 1
    CHA_CHA_20 = 2


class EventCode(Enum):
    ITEM_CREATE = 1
    ITEM_DELETE = 2
    ITEM_NAME_CHANGE = 3
    MESSAGE_SENT = 4
    ITEM_MOVED = 5
    ITEM_PREVIEW_INFO_ADD = 6
    FORCE_FOLDER_NAVIGATION = 7
    FOLDER_LOCK_STATUS_CHANGE = 8
    ITEM_MOVE_TO_TRASH = 9
    ITEM_RESTORE_FROM_TRASH = 10
