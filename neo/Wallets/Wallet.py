# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from neo.Wallets.Wallet import Wallet
"""

from neo.Helper import ANTCOIN
from neo.Defaults import TEST_ADDRESS
from neo.Core.TX.Transaction import TransactionOutput,TransactionInput,TransactionType
from neo.Core.CoinState import CoinState
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Cryptography.Base58 import b58decode
from neo.Cryptography.Crypto import *
from neo.Cryptography.Helper import *
from neo.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet
from neo.Wallets.Account import Account
from neo.Wallets.Contract import Contract
from neo.Wallets.AddressState import AddressState
from neo.Wallets.Coin import Coin
from neo.Network.RemoteNode import RemoteNode
from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryWriter import BinaryWriter
from neo import Settings

import itertools
import hashlib
from ecdsa import SigningKey, NIST256p
from neo.Defaults import TEST_NODE
from bitarray import bitarray

from threading import Thread
from threading import Lock


from Crypto import Random
from Crypto.Cipher import AES

class Wallet(object):



    AddressVersion = Settings.ADDRESS_VERSION

    _path = ''
    _iv = None
    _master_key = None
    _keys = {} #holds keypairs
    _contracts = {} #holds Contracts

    _watch_only = set() # holds set of hashes
    _coins = [] #holds Coin References

    _current_height=0

    _is_running = True
    _db_path = _path

    _indexedDB = None
    _node = None

    _blockThread = None
    _lock = Lock()

    @property
    def WalletHeight(self):
        return self._current_height




    """docstring for Wallet"""
    def __init__(self, path, passwordKey, create):

        if create:
            self._path = path
            self._iv = bitarray(16)
            self._master_key = bitarray(32)
            self._keys = []
            self._indexedDB= IndexedDBWallet()
            self._node = RemoteNode(url=TEST_NODE)

            self._current_height = Blockchain.Default().HeaderHeight + 1 if Blockchain.Default() is not None else 0

            self.BuildDatabase()

            self._iv = Random.new().read(self._iv)
            self._master_key = Random.new().read(self._master_key)


            self.SaveStoredData('PasswordHash', hashlib.sha256(passwordKey))
            self.SaveStoredData('IV', self._iv),
            self.SaveStoredData('MasterKey', AES.new(self._master_key, AES.MODE_CBC, self._iv))
    #        self.SaveStoredData('Version') { Version.Major, Version.Minor, Version.Build, Version.Revision }.Select(p => BitConverter.GetBytes(p)).SelectMany(p => p).ToArray());
            self.SaveStoredData('Height', self._current_height)

        else:

            passwordHash = self.LoadStoredData('PasswordHash')
            if passwordHash is not None and passwordHash != hashlib.sha256(passwordKey):
                raise Exception("Cryptographic exception")

            self._iv = self.LoadStoredData('IV')
            self._master_key = self.LoadStoredData('MasterKey')
            self._keys = self.LoadKeyPair()
            self._contracts = self.LoadContracts()
            self._watch_only = self.LoadWatchOnly()
            self._coins = self.LoadCoins()
            self._current_height = self.LoadStoredData('Height')

            del passwordKey

            self._blockThread = Thread(target=self.ProcessBlocks, name='Wallet.ProcessBlocks')
            self._blockThread.start()

    def BuildDatabase(self):
        #abstract
        pass


    def AddContract(self, contract):

#        found=False
#        for key in self._key_pair:
#            if key.
        raise NotImplementedError()

    def SaveStoredData(self, key, value):

        raise NotImplementedError()

    def LoadStoredData(self, key):
        raise NotImplementedError()

    def LoadKeyPair(self):

#        raise NotImplementedError()
        return []

    def LoadContracts(self):
#        raise NotImplementedError()
        return []


    def LoadWatchOnly(self):
#        raise NotImplementedError()
        return set()

    def LoadCoins(self):
#        raise NotImplementedError()
        return []


    def ProcessBlocks(self):
        while self._is_running:

            while self._current_height <= Blockchain.Default().Height and self._is_running:

                block = Blockchain.Default().GetBlock(self._current_height)

                if block is not None:
                    self.ProcessNewBlock(block)

            for i in range(0, 20):
                if self._is_running:
                    time.sleep(1)

    def ProcessNewBlock(self, block):

        added = set()
        changed = set()
        deleted = set()

        self._lock.acquire()
        try:

            for tx in block.Transactions:

                for index,output in enumerate(tx.outputs):

                    state = self.CheckAddressState(output.ScriptHash)

                    if state > 0:
                        key = CoinReference(tx.Hash, index )

                        found=False
                        for coin in self._coins:
                            if coin.CoinRef.Equals(key):
                                coin.State |= CoinState.Confirmed
                                changed.add(coin.CoinRef)
                                found = True
                        if not found:
                            newcoin = Coin.CoinFromRef(key, output, state=CoinState.Confirmed )
                            self._coins.append(newcoin)
                            added.add(newcoin.CoinRef)

                        if state == AddressState.WatchOnly:
                            for coin in self._coins:
                                if coin.CoinRef.Equals(key):
                                    coin.State |= CoinState.WatchOnly
                                    changed.add(coin.CoinRef)

            for tx in block.Transactions:

                for input in tx.inputs:

                    for coin in self._coins:
                        if coin.CoinRef.Equals(input):

                            if coin.TXOutput.AssetId == Blockchain.SystemShare().Hash():
                                coin.State |= CoinState.Spent | CoinState.Confirmed
                                changed.add(coin.CoinRef)
                            else:
                                self._coins.remove(coin)
                                deleted.add(coin.CoinRef)

            for claimTx in [tx for tx in block.Transactions if tx.Type == TransactionType.ClaimTransaction]:
                for ref in claimTx.Claims:
                    if ref in self._coins:
                        self._coins.remove(ref)
                        deleted.add(ref)

            self._current_height+=1
            self.OnProcessNewBlock(block, added, changed, deleted)

            if len(added) + len(deleted) + len(changed) > 0:
                self.BalanceChanged()

        except Exception as e:
            print("could not process: %s " % e)
        finally:
            self._lock.release()


    def Rebuild(self):
        self._lock.acquire()
        self._coins = []
        self._current_height = 0
        self._lock.release()



    def OnProcessNewBlock(self, block, added, changed, deleted):
        # abstract
        pass

    def BalanceChanged(self):
        # abstract
        pass

    def CheckAddressState(self, script_hash):
        for contract in self._contracts:
            if contract.ScriptHash == script_hash:
                return AddressState.InWallet
        for watch in self._watch_only:
            if watch.ScriptHash == script_hash:
                return AddressState.WatchOnly
        return AddressState.NoState

    @staticmethod
    def ToAddress(scripthash):
        return scripthash_to_address(scripthash)

    def ToScriptHash(self, address):
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != self.AddressVersion:
            raise ValueError('Not correct Coin Version')
        scriptHash = binascii.hexlify(data[1:21])
        if Wallet.ToAddress(scriptHash) == address:
            return scriptHash
        else:
            raise ValueError('Not correct Address, something wrong in Address[-4:].')

    def ValidatePassword(self, password):
        return hashlib.sha256(password) == self.LoadStoredData('PasswordHash')

    def FindUnSpentCoins(self, scriptHash):
        """:return: Coin[]"""
        return self.indexeddb.findCoins(self.ToAddress(scriptHash), status=CoinState.Unspent)

    def MakeTransaction(self, tx, account):
        """Make Transaction"""
        if tx.outputs == None:
            raise ValueError('Not correct Address, wrong length.')

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
        contract.CreateSignatureContract(account.publicKey)
        Redeem_script = contract.RedeemScript

        # Add Signature
        sk = SigningKey.from_string(binascii.unhexlify(account.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
        signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
        regtx = reg_tx + '014140' + signature + '23' + Redeem_script
        # sendRawTransaction
        print(regtx)
        response = self.node.sendRawTransaction(regtx)
        import json
        print(response)
        return txid

    def selectInputs(self, outputs, coins, account, fee):

        scripthash = account.scriptHash

        if len(outputs) > 1 and len(coins) < 1:
            raise Exception('Not Enought Coins')

        # Count the total amount of change
        coin = itertools.groupby(sorted(coins, key=lambda x: x.asset), lambda x: x.asset)
        coin_total = dict([(k, sum(int(x.value) for x in g)) for k,g in coin])

        # Count the pay total
        pays = itertools.groupby(sorted(outputs, key=lambda x: x.AssetId), lambda x: x.AssetId)
        pays_total = dict([(k, sum(int(x.Value) for x in g)) for k,g in pays])

        if int(fee.f) > 0:
            if ANTCOIN in iter(list(pays_total.keys())):
                pays_total[ANTCOIN] += int(fee.f)
            else:
                pays_total[ANTCOIN] = int(fee.f)

        # Check whether there is enough change
        for asset, value in list(pays_total.items()):
            if asset not in coin_total:
                raise Exception('Coins does not contain asset {asset}.'.format(asset=asset))

            if coin_total.get(asset) - value < 0:
                raise Exception('Coins does not have enough asset {asset}, need {amount}.'.format(asset=asset, amount=value))

        # res: used Coins
        # change: change in outpus
        res = []
        change = []

        # Copy the parms
        _coins  = coins[:]

        # Find whether have the same value of change
        for asset, value in list(pays_total.items()):
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
        print(total)
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


def __test():
    wallet = Wallet()
    coins = wallet.indexeddb.loadCoins(address=TEST_ADDRESS,asset='dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9')
    #print coins
    print('test1: select the min max coin')
    outputs = [{'work_id':'12687','amount':80}, {'work_id':'12689','amount':100}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print(i)
    print('test2: select the equal coin')
    outputs = [{'work_id':'12687','amount':1},]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print(i)
    print('test3: select the min(max coins)')
    outputs = [{'work_id':'12687','amount':232},{'work_id':'12689','amount':10}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print(i)
    print('test4: select none coin')
    outputs = [{'work_id':'12687','amount':10000},{'work_id':'12689','amount':10}]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print(i)
    print('test5: select the min max coin')
    outputs = [{'work_id':'12687','amount':2},]
    inputs = wallet.selectCoins(coins,outputs)
    for i in inputs:
        print(i)

if __name__ == '__main__':
    __test()
