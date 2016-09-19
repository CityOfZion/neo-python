# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from AntShares.Wallets.Wallet import Wallet
"""


from AntShares.Cryptography.Base58 import b58decode
from AntShares.Helper import big_or_little
from AntShares.Cryptography.Helper import *
from AntShares.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet

import urllib
import json
import itertools


def getInputs():
    html = urllib.urlopen("%s%s"%(URL,ADDR))
    content = html.read()
    res = json.loads(content)
    if res.get(u'message', u'error') == u'success':
        data = res.get(u'data', {})
        return sorted(data.iteritems(), key=lambda x:x[1]['value'], reverse=True)
    return res.get(u'message', u'error')


class Wallet(object):
    """docstring for Wallet"""
    def __init__(self):
        super(Wallet, self).__init__()
        self.current_height = 0
        self.isrunning = True
        self.isclosed = False
        self.indexeddb = IndexedDBWallet()

    def getCoinVersion(self):
        return chr(0x17)

    def getWalletHeight(self):  # Need or Not?
        return self.current_height

    def toAddress(self, scripthash):
        return scripthash_to_address(scripthash)

    def getInputs(self, scriptHash):
        """
        :return: Coin[]"""
        return self.indexeddb.loadCoins(self.toAddress(criptHash))

    def makeTransaction(self, tx):
        if tx.outputs == None:
            raise ValueError, 'Not correct Address, wrong length.'
        if tx.attributes == None:
            tx.attributes = []

        inputs = self.getInputs(scriptHash)
        inputs, coins, outputs = self.selectInputs(inputs, tx.outputs)

    def selectInputs(self, outputs, inputs):

        if len(outputs) > 1 and len(inputs) < 1:
            raise Exception, 'Not Enought Inputs'

        # Count the total amount of change
        coin = itertools.groupby(sorted(inputs, key=lambda x: x[1]['type']), lambda x: x[1]['type'])
        coin_total = dict([(k, sum(int(x[1]['value']) for x in g)) for k,g in coin])

        # Count the pay total
        pays = itertools.groupby(sorted(outputs, key=lambda x: x['Asset']), lambda x: x['Asset'])
        pays_total = dict([(k, sum(int(x['Value']) for x in g)) for k,g in pays])

        # Check whether there is enough change
        for asset, value in pays_total.iteritems():
            if not coin_total.has_key(asset):
                raise Exception, 'Inputs does not contain asset {asset}.'.format(asset=asset)

            if coin_total.get(asset) - value < 0:
                raise Exception, 'Inputs does not have enough asset {asset}, need {amount}.'.format(asset=asset, amount=value)

        # res: used inputs
        # change: change in outpus
        res = []
        change = []

        # Copy the parms
        _inputs  = inputs[:]

        # Find whether have the same value of change
        for asset, value in pays_total.iteritems():
            for _input in _inputs:
                if asset == _input[1]['type'] and value == int(_input[1]['value']):
                    # Find the coin
                    res.append(_input)
                    _inputs.remove(_input)
                    break

            else:
                # Find the affordable change

                affordable = sorted([i for i in _inputs if i[1]['type'] == asset and int(i[1]['value']) >= value],
                                    key=lambda x: int(x[1]['value']))

                # Use the minimum if exists
                if len(affordable) > 0:
                    res.append(affordable[0])
                    _inputs.remove(affordable[0])

                    # If the amout > value, set the change
                    amount = int(affordable[0][1]['value'])
                    if amount > value:
                        change.append({'Asset': asset, 'Value': str(amount-value), 'Scripthash': getChangeAddr()})

                else:
                    # Calculate the rest of coins
                    rest = sorted([i for i in _inputs if i[1]['type'] == asset],
                                  key=lambda x: int(x[1]['value']),
                                  reverse=True)

                    amount = 0
                    for _input in rest:
                        amount += int(_input[1]['value'])
                        res.append(_input)
                        _inputs.remove(_input)
                        if amount == value:
                            break
                        elif amount > value:
                            # If the amout > value, set the change
                            change.append({'Asset': asset, 'Value': str(amount-value), 'Scripthash': getChangeAddr()})
                            break

        return res, _inputs, outputs + change

    def selectCoins(self, coins, outputs):
        """the simplest alg of selecting coins"""
        total = sum([int(out['amount']) for out in outputs])
        cs = sorted(coins,key=lambda c:c.value,reverse=True)
        print total
        inputs = []
        # has no enough coins
        if sum([int(c.value) for c in coins]) < total:
            return inputs
        for i in range(len(cs)):
            #step 1: find the coin with value==total
            if cs[i].value == total:
                inputs = [cs[i],]
                break
            #step 2: find the min coin with value>total
            if cs[0].value > total and cs[i].value<total:
                inputs = [cs[i-1],]
                break
            #step 3: find the min(max coins) with sum(coins)>= total
            inputs.append(cs[i])
            if cs[0].value<total and sum([i.value for i in inputs]) >= total:
                break
        return inputs

    def addressToScriptHash(self, address):
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError, 'Not correct Address, wrong length.'
        if data[0] != self.getCoinVersion():
            raise ValueError, 'Not correct CoivVersion'
        scriptHash = binascii.hexlify(data[1:21])
        if self.toAddress(scriptHash) == address:
            return scriptHash
        else:
            raise ValueError, 'Not correct Address, something wrong in Address[-4:].'

    def createAccount(self):
        return Account()

    def getAccount(self, privKey=None):
        return Account(privKey)

def __test():
    wallet = Wallet()
    coins = wallet.indexeddb.loadCoins(address='AYbVqnhpPUPaA886gSUYfoi2qiFeJUQZLi',asset='dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9')
    #print coins
    print 'test1: select the min max coin'
    outputs = [{'work_id':'12687','amount':80}, {'work_id':'12689','amount':100}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print i
    print 'test2: select the equal coin'
    outputs = [{'work_id':'12687','amount':1},]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print i
    print 'test3: select the min(max coins)'
    outputs = [{'work_id':'12687','amount':232},{'work_id':'12689','amount':10}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print i
    print 'test4: select none coin'
    outputs = [{'work_id':'12687','amount':10000},{'work_id':'12689','amount':10}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print i
    print 'test5: select the min max coin'
    outputs = [{'work_id':'12687','amount':2},]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print i

if __name__ == '__main__':
    import sys
    sys.path.append('/home/ecoin/antshares-python/sdk/')
    __test()
