from enum import Enum


class EncryptionMethod(Enum):
    Not_Encrypted = 0
    AES_CTR = 1
    CHA_CHA_20 = 2


class EventType(Enum):
    ITEM_CREATE = 1
    ITEM_DELETE = 2
    ITEM_UPDATE = 3
    ITEM_MOVE_OUT = 4
    ITEM_MOVE_IN = 5
    ITEM_MOVE_TO_TRASH = 6
    ITEM_RESTORE_FROM_TRASH = 7
    MESSAGE_UPDATE = 8
    MESSAGE_SENT = 9
    FOLDER_LOCK_STATUS_CHANGE = 10
    FORCE_LOGOUT = 11
    NEW_DEVICE_LOG_IN = 12

