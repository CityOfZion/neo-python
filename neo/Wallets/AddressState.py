from enum import IntEnum


class AddressState(IntEnum):
    NoState = 0
    InWallet = 1
    WatchOnly = 2
