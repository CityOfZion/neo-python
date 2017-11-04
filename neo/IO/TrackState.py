from enum import Enum


class TrackState(Enum):
    NoState = 0x00
    Added = 0x01
    Changed = 0x02
    Deleted = 0x03
