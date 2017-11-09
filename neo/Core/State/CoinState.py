from enum import IntEnum


class CoinState(IntEnum):
    Unconfirmed = 0
    Confirmed = 1 << 0
    Spent = 1 << 1
#    Vote = 1 << 2
    Claimed = 1 << 3
    Locked = 1 << 4
    Frozen = 1 << 5
    WatchOnly = 1 << 6
