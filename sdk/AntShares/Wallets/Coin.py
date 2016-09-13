# -*- coding:utf-8 -*-
"""
Description:
    define the data struct of coin 
Usage:
    from AntShares.Wallets.Coin import Coin 
"""

class Coin():
    def __init__(self,txid,idx,value,asset,address,status):
        self.txid = txid
        self.idx = idx
        self.value = value
        self.asset = asset
        self.address = address
        self.status = status 

