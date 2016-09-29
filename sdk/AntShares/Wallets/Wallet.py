# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from AntShares.Wallets.Wallet import Wallet
"""

from AntShares.Helper import ANTCOIN, big_or_little

from AntShares.Core.RegisterTransaction import RegisterTransaction
from AntShares.Core.IssueTransaction import IssueTransaction
from AntShares.Core.TransactionOutput import TransactionOutput
from AntShares.Core.TransactionInput import TransactionInput

from AntShares.Cryptography.Base58 import b58decode
from AntShares.Cryptography.Helper import *

from AntShares.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet

from AntShares.Wallets.Account import Account
from AntShares.Wallets.Coin import Coin
from AntShares.Wallets.CoinState import CoinState
from AntShares.Wallets.Contract import Contract

from AntShares.Network.RemoteNode import RemoteNode

from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

import itertools
from ecdsa import SigningKey, NIST256p


class Wallet(object):
    """docstring for Wallet"""
    def __init__(self):
        super(Wallet, self).__init__()
        self.current_height = 0
        self.isrunning = True
        self.isclosed = False
        self.indexeddb = IndexedDBWallet()
        self.node = RemoteNode(url='http://10.84.136.112:20332')

    def getCoinVersion(self):
        return chr(0x17)

    def getWalletHeight(self):  # Need or Not?
        return self.current_height

    def toAddress(self, scripthash):
        return scripthash_to_address(scripthash)

    def findUnSpentCoins(self, scriptHash):
        """
        :return: Coin[]"""
        return self.indexeddb.findCoins(self.toAddress(scriptHash), status=CoinState.Unspent)

    def makeTransaction(self, tx, account):
        """Make Transaction"""
        if tx.outputs == None:
            raise ValueError, 'Not correct Address, wrong length.'

        if tx.attributes == None:
            tx.attributes = []

        coins = self.findUnSpentCoins(account.scriptHash)
        tx.inputs, tx.outputs = self.selectInputs(tx.outputs, coins, account, tx.systemFee)

        # Make transaction
        stream = MemoryStream()
        writer = BinaryWriter(stream)
        tx.serializeUnsigned(writer)
        reg_tx = stream.toArray()
        tx.ensureHash()
        txid = tx.hash

        # RedeenScript
        contract = Contract()
        contract.createSignatureContract(account.publicKey)
        Redeem_script = contract.redeemScript

        # Add Signature
        sk = SigningKey.from_string(binascii.unhexlify(account.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
        signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
        regtx = reg_tx + '014140' + signature + '23' + Redeem_script
        # sendRawTransaction
        print regtx
        response = self.node.sendRawTransaction(regtx)
        import json
        print response
        return txid

    def selectInputs(self, outputs, coins, account, fee):

        scripthash = account.scriptHash

        if len(outputs) > 1 and len(coins) < 1:
            raise Exception, 'Not Enought Coins'

        # Count the total amount of change
        coin = itertools.groupby(sorted(coins, key=lambda x: x.asset), lambda x: x.asset)
        coin_total = dict([(k, sum(int(x.value) for x in g)) for k,g in coin])

        # Count the pay total
        pays = itertools.groupby(sorted(outputs, key=lambda x: x.AssetId), lambda x: x.AssetId)
        pays_total = dict([(k, sum(int(x.Value) for x in g)) for k,g in pays])

        if int(fee.f) > 0:
            if ANTCOIN in pays_total.iterkeys():
                pays_total[ANTCOIN] += int(fee.f)
            else:
                pays_total[ANTCOIN] = int(fee.f)

        # Check whether there is enough change
        for asset, value in pays_total.iteritems():
            if not coin_total.has_key(asset):
                raise Exception, 'Coins does not contain asset {asset}.'.format(asset=asset)

            if coin_total.get(asset) - value < 0:
                raise Exception, 'Coins does not have enough asset {asset}, need {amount}.'.format(asset=asset, amount=value)

        # res: used Coins
        # change: change in outpus
        res = []
        change = []

        # Copy the parms
        _coins  = coins[:]

        # Find whether have the same value of change
        for asset, value in pays_total.iteritems():
            for _coin in _coins:
                if asset == _coin.asset and value == int(_coin.value):
                    # Find the coin
                    res.append(TransactionInput(prevHash=_coin.txid, prevIndex=_coin.idx))
                    _coins.remove(_coin)
                    break

            else:
                # Find the affordable change

                affordable = sorted([i for i in _coins if i.asset == asset and int(i.value) >= value],
                                    key=lambda x: int(x.value))

                # Use the minimum if exists
                if len(affordable) > 0:
                    res.append(TransactionInput(prevHash=affordable[0].txid, prevIndex=affordable[0].idx))
                    _coins.remove(affordable[0])

                    # If the amout > value, set the change
                    amount = int(affordable[0].value)
                    if amount > value:
                        change.append(TransactionOutput(AssetId=asset, Value=str(amount-value), ScriptHash=scripthash))

                else:
                    # Calculate the rest of coins
                    rest = sorted([i for i in _coins if i.asset == asset],
                                  key=lambda x: int(x.value),
                                  reverse=True)

                    amount = 0
                    for _coin in rest:
                        amount += int(_coin.value)
                        res.append(TransactionInput(prevHash=_coin.txid, prevIndex=_coin.idx))
                        _coins.remove(_coin)
                        if amount == value:
                            break
                        elif amount > value:
                            # If the amout > value, set the change
                            change.append(TransactionOutput(AssetId=asset, Value=str(amount-value), ScriptHash=scripthash))
                            break

        return res, outputs + change

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
