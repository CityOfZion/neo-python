#!/usr/bin/env python

import sys
sys.path.append('/home/ecoin/bcmw/antshares-python/sdk/')

import config
from DbContext import Mongodb
from AntShares.Wallets.Coin import Coin
from AntShares.Wallets.CoinState import CoinState

class IndexedDBWallet():
    def __init__(self):
        self.mongo  = Mongodb(host=config.bcdb.host, port=config.bcdb.port)

    def loadCoins(self,address):
        qry = {'address':address,'status':CoinState.Unspent}
        items = self.mongo.read('coins',qry)
        coins = []
        for i in items:
            c = Coin(txid=i['txid'],idx = i['idx'],value=i['value'],asset=i['asset'], address=i['address'],status=i['status']) 
            coins.append(c)
        return coins

    def onSendTransaction(self,spending,incomeing):
        for c in spending:
            qry = {'txid':c.txid,'idx':c.idx}
            self.mongo.update('coins', qry,{'$set':{'status':CoinState.Spending}}) 
        for c in incoming:
            qry = {'txid':c.txid,'idx':c.idx}
            item['txid'] = c.txid
            item['idx'] = c.idx
            item['value'] = c.value
            item['address'] = c.address
            item['asset'] = c.asset
            item['status'] = CoinState.Unconfirmed 
            self.mongo.replace('coins', qry, item) 
        

def __test():
    address = 'Adpd2LoUndjEWvdRVrk4SDnAAJ9hM2GgYP'
    wallet = IndexedDBWallet()
    coins = wallet.loadCoins(address)
    print coins

if __name__ == '__main__':
    __test()

