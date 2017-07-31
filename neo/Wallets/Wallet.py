# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from neo.Wallets.Wallet import Wallet
"""

from neo.Defaults import LDB_PATH
from neo.Core.TX.Transaction import TransactionType
from neo.Core.CoinState import CoinState
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Cryptography.Base58 import b58decode
from neo.Cryptography.Helper import *
from neo.Wallets.AddressState import AddressState
from neo.Wallets.Coin import Coin
from neo.Wallets.KeyPair import KeyPair
from neo import Settings
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from autologging import logged
import hashlib

from threading import Thread
from threading import Lock


from Crypto import Random
from Crypto.Cipher import AES

@logged
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
    #_node = None

    _blockThread = None
    _lock = Lock()

    @property
    def WalletHeight(self):
        return self._current_height




    """docstring for Wallet"""
    def __init__(self, path, passwordKey, create):

        if create:
            self._path = path
            self._iv = bytes( Random.get_random_bytes(16))
            self._master_key = bytes(Random.get_random_bytes(32))
            self._keys = []
            self._indexedDB= LevelDBBlockchain(LDB_PATH)
            #self._node = RemoteNode(url=TEST_NODE)

            self._current_height = Blockchain.Default().HeaderHeight() + 1 if Blockchain.Default() is not None else 0

            self.BuildDatabase()

            print("iv::: %s " % self._iv)
            print("mk::: A%s " % self._master_key)

            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            master = AES.new(self._master_key, AES.MODE_CBC, self._iv)
            masterKey = master.encrypt(passwordHash)
            self.SaveStoredData('PasswordHash', passwordHash)
            self.SaveStoredData('IV', self._iv),
            self.SaveStoredData('MasterKey', masterKey)
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


            self._current_height = Blockchain.Default().HeaderHeight() + 1 if Blockchain.Default() is not None else 0

            self._blockThread = Thread(target=self.ProcessBlocks, name='Wallet.ProcessBlocks')
            self._blockThread.start()

    def BuildDatabase(self):
        #abstract
        pass


    def AddContract(self, contract):

        for key in self._keys:
            if not key.PublicKeyHash == contract.PublicKeyHash:
                raise Exception('Invalid operation- public key mismatch')

        self._contracts[contract.ScriptHash] = contract
        self._watch_only.remove(contract.ScriptHash)


    def AddWatchOnly(self, script_hash):

        if script_hash in self._contracts:
            return

        self._watch_only.add(script_hash)


    def ChangePassword(self, password_old, password_new):
        if not self.ValidatePassword(password_old):
            return False

        password_key = hashlib.sha256(password_new)
        self.SaveStoredData("PasswordHash", password_key)
        self.SaveStoredData("MasterKey", AES.new(self._master_key, AES.MODE_CBC, self._iv))



    def ContainsKey(self, public_key):
        raise NotImplementedError()

    def ContainsKeyHash(self, public_key_hash):
        return public_key_hash in self._keys

    def ContainsAddress(self, script_hash):
        return self.CheckAddressState(script_hash) >= AddressState.InWallet


    def CreatePrivateKey(self):
        private_key = bytearray(32)
        private_key = Random.new().read(private_key)
        return private_key

    def CreateKeyPairFromPrivateKey(self, private_key):

        keypair = KeyPair(private_key = private_key)

        self._keys[keypair.PublicKeyHash] = keypair

        return keypair

    def DecryptPrivateKey(self, encrypted_private_key):
        raise NotImplementedError()

    def DeleteKey(self, public_key_hash):
        raise NotImplementedError()

    def DeleteAddress(self, script_hash):
        raise NotImplementedError()



    def FindUnspentCoins(self):
        unspent = []
        for coin in self._coins:
            if coin.State == CoinState.Confirmed:
                unspent.append(coin)
        return unspent

    def GetKey(self, public_key_hash):
        if public_key_hash in self._keys:
            return self._keys[public_key_hash]
        return None

    def GetAvailable(self, asset_id):
        raise NotImplementedError()

    def GetBalance(self, asset_id):
        raise NotImplementedError()


    def SaveStoredData(self, key, value):
        # abstract
        pass

    def LoadStoredData(self, key):
        # abstract
        pass

    def LoadKeyPair(self):
        #abstract
        pass

    def LoadContracts(self):
        # abstract
        pass

    def LoadWatchOnly(self):
        # abstract
        pass


    def LoadCoins(self):
        # abstract
        pass

    def ProcessBlocks(self):
        while self._is_running:

            while self._current_height <= Blockchain.Default().Height() and self._is_running:

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


    def MakeTransaction(self, tx, account):

        raise NotImplementedError()


