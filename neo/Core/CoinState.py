from enum import IntEnum

class CoinState(IntEnum):
    Unconfirmed = 0
    Confirmed = 1
    Spent = 2
    Claimed = 3
    Locked = 4
    Frozen = 5
    WatchOnly = 6

