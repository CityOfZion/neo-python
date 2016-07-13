# -*- coding:utf-8 -*-
"""
Description:
    CoinState in AntShares.Wallets
Usage:
    from AntShares.Wallets.CoinState import CoinState
"""


class CoinState(object):
    Unconfirmed = 0x00
    Unspent = 0x01
    Spending = 0x02
    Spent = 0x03
    SpentAndClaimed = 0x04
