from enum import Enum, auto, unique


@unique
class VMFault(Enum):
    UNKNOWN1 = auto()
    INVALID_JUMP = auto()
    UNKNOWN2 = auto()
    INVALID_CONTRACT = auto()
    SYSCALL_ERROR = auto()
    UNKNOWN3 = auto()
    UNKNOWN4 = auto()
    UNKNOWN5 = auto()
    UNKNOWN6 = auto()
    SUBSTR_INVALID_LENGTH = auto()
    SUBSTR_INVALID_INDEX = auto()
    LEFT_INVALID_COUNT = auto()
    RIGHT_INVALID_COUNT = auto()
    RIGHT_UNKNOWN = auto()
    CHECKMULTISIG_INVALID_PUBLICKEY_COUNT = auto()
    CHECKMULTISIG_SIGNATURE_ERROR = auto()
    UNKNOWN7 = auto()
    UNKNOWN8 = auto()
    UNPACK_INVALID_TYPE = auto()
    PICKITEM_NEGATIVE_INDEX = auto()
    PICKITEM_INVALID_TYPE = auto()
    PICKITEM_INVALID_INDEX = auto()
    SETITEM_INVALID_TYPE = auto()
    SETITEM_INVALID_INDEX = auto()
    APPEND_INVALID_TYPE = auto()
    REVERSE_INVALID_TYPE = auto()
    REMOVE_INVALID_TYPE = auto()
    REMOVE_INVALID_INDEX = auto()
    POP_ITEM_NOT_ARRAY = auto()

    DICT_KEY_NOT_FOUND = auto()

    DICT_KEY_ERROR = auto()

    KEY_IS_COLLECTION = auto()

    THROW = auto()
    THROWIFNOT = auto()
    UNKNOWN_OPCODE = auto()

    UNKNOWN_STACKISOLATION = auto()
    UNKNOWN_STACKISOLATION2 = auto()
    UNKNOWN_STACKISOLATION3 = auto()
