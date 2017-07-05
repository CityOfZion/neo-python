# -*- coding:utf-8 -*-
"""
Description:
    define the data struct of coin
Usage:
    from AntShares.Wallets.Coin import Coin
"""


class Coin():
    def __init__(self, txid, idx, value, asset, address, status):
        self.txid = txid
        self.idx = idx
        self.value = value
        self.asset = asset
        self.address = address
        self.status = status

    def __str__(self):
        s = 'txid:%s, idx:%d, value:%d, asset:%s, address:%s, status:%d' % (self.txid, self.idx, self.value, self.asset, self.address, self.status)
        return s

def __test():
    from CoinState import CoinState
    coin = Coin(txid='132555', idx=0, value=100, asset='asdfadfa', address='aadfadf', status=CoinState.Unspent)
    print coin.__str__()

if __name__ == '__main__':
    __test()
