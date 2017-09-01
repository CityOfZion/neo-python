# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from neo.Wallets.Wallet import Wallet
"""

from neo.Core.TX.Transaction import TransactionType
from neo.Core.State.CoinState import CoinState
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
from neo import Settings
from threading import Thread
from threading import Lock
import traceback


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
    _coins = {} #holds Coin References

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

        self._path = path

        if create:
            self._iv = bytes( Random.get_random_bytes(16))
            self._master_key = bytes(Random.get_random_bytes(32))
            self._keys = {}
            self._contracts = {}
            self._coins = {}

            if Blockchain.Default() is None:
                self._indexedDB= LevelDBBlockchain(Settings.LEVELDB_PATH)
                Blockchain.RegisterBlockchain(self._indexedDB)
            else:
                self._indexedDB = Blockchain.Default()
            #self._node = RemoteNode(url=TEST_NODE)

            self._current_height = 0

            self.BuildDatabase()

            self.__log.debug("iv::: %s " % self._iv)
            self.__log.debug("mk::: A%s " % self._master_key)

            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            master = AES.new(self._master_key, AES.MODE_CBC, self._iv)
            masterKey = master.encrypt(passwordHash)
            self.SaveStoredData('PasswordHash', passwordHash)
            self.SaveStoredData('IV', self._iv),
            self.SaveStoredData('MasterKey', masterKey)
    #        self.SaveStoredData('Version') { Version.Major, Version.Minor, Version.Build, Version.Revision }.Select(p => BitConverter.GetBytes(p)).SelectMany(p => p).ToArray());
            self.SaveStoredData('Height', self._current_height.to_bytes(4, 'little'))

        else:
            self.BuildDatabase()

            passwordHash = self.LoadStoredData('PasswordHash')
            if passwordHash is None:
                raise Exception("Password hash not found in database")

            hkey= hashlib.sha256(passwordKey.encode('utf-8'))

            if passwordHash is not None and passwordHash != hashlib.sha256(passwordKey.encode('utf-8')).digest():
                raise Exception("Incorrect Password")

            self._iv = self.LoadStoredData('IV')
            self._master_key = self.LoadStoredData('MasterKey')
            self._keys = self.LoadKeyPair()
            self._contracts = self.LoadContracts()
            self._watch_only = self.LoadWatchOnly()
            self._coins = self.LoadCoins()
            try:
                h = self.LoadStoredData('Height')
                self._current_height = int.from_bytes(h, 'little')
            except Exception as e:
                print("couldnt load height data %s " % e)
                self._current_height = 0

            self._current_height = 470000

            del passwordKey




    def BuildDatabase(self):
        #abstract
        pass


    def AddContract(self, contract):

        if not contract.PublicKeyHash.ToBytes() in self._keys.keys():
            raise Exception('Invalid operation- public key mismatch')

        self._contracts[contract.ScriptHash.ToBytes()] = contract
        if contract.ScriptHash.ToBytes() in self._watch_only:
            self._watch_only.remove(contract.ScriptHash.ToBytes())


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


    def CreateKey(self):
        private_key = bytes(Random.get_random_bytes(32))
        self.__log.debug("private key %s " % private_key)

        key = KeyPair(priv_key = private_key)
        self._keys[key.PublicKeyHash] = key
        self.__log.debug("keys %s " % self._keys.items())
        return key
 #       return private_key

#    def CreateKeyPairFromPrivateKey(self, private_key):
#
 #       keypair = KeyPair(private_key = private_key)

   #     self._keys[keypair.PublicKeyHash] = keypair

#        return keypair


    def EncryptPrivateKey(self, decrypted):
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)

        return aes.encrypt(decrypted)

    def DecryptPrivateKey(self, encrypted_private_key):
        raise NotImplementedError()

    def DeleteKey(self, public_key_hash):
        raise NotImplementedError()

    def DeleteAddress(self, script_hash):
        raise NotImplementedError()



    def FindUnspentCoins(self):
        unspent = []
        for key,coin in self._coins.items():
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

#        start = time.clock()
        blockcount = 0

        while self._current_height <= Blockchain.Default().Height and self._is_running and blockcount < 500:

            block = Blockchain.Default().GetBlockByHeight(self._current_height)

            if block is not None:
                self.ProcessNewBlock(block)

            blockcount+=1

        self.SaveStoredData("Height", self._current_height.to_bytes(8, 'little'))
        self.__log.debug("Wallet processed block to %s " % self._current_height)
#        end = time.clock()

    def ProcessNewBlock(self, block):

        added = set()
        changed = set()
        deleted = set()

#        self.__log.debug("Wallet processing block %s " % block.Index)
        try:

            for tx in block.FullTransactions:

                for index,output in enumerate(tx.outputs):
                    state = self.CheckAddressState(output.ScriptHash)

                    if state & AddressState.InWallet > 0:

                        key = CoinReference(tx.Hash, index)

                        if key in self._coins.keys():
                            coin = self._coins[key]
                            coin.State |= CoinState.Confirmed
                            changed.add(coin)

                        else:
                            newcoin = Coin.CoinFromRef(coin_ref=key,tx_output=output, state=CoinState.Confirmed)
#                            newcoin = Coin.CoinFromRef(key, output, state=CoinState.Confirmed )
                            self._coins[key] = newcoin
                            added.add(newcoin)

                        if state & AddressState.WatchOnly > 0:
                            self._coins[key].State |= CoinState.WatchOnly
                            changed.add(self._coins[key])


            for tx in block.FullTransactions:

                for input in tx.inputs:

                    if input in self._coins.keys():

                        if self._coins[input].Output.AssetId.ToBytes() == Blockchain.SystemShare().Hash.ToBytes():
                            self._coins[input].State |= CoinState.Spent | CoinState.Confirmed
                            changed.add(self._coins[input])
                        else:
                            deleted.add(self._coins[input])
                            del self._coins[input]


            for claimTx in [tx for tx in block.Transactions if tx.Type == TransactionType.ClaimTransaction]:

                for ref in claimTx.Claims:
                    if ref in self._coins.keys():
                        deleted.add(self._coins[ref])
                        del self._coins[ref]

            self._current_height+=1
            self.OnProcessNewBlock(block, added, changed, deleted)

            if len(added) + len(deleted) + len(changed) > 0:
                self.BalanceChanged()

        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            print("could not process %s " % e)


    def Rebuild(self):
        self._coins = {}
        self._current_height = 0



    def OnProcessNewBlock(self, block, added, changed, deleted):
        # abstract
        pass

    def BalanceChanged(self):
        # abstract
        pass

    def IsWalletTransaction(self, tx):
        for key,contract in self._contracts.items():

            for output in tx.outputs:
                if output.ScriptHash.ToBytes() == contract.ScriptHash.ToBytes():
                    return True

            for script in tx.scripts:

                if script.VerificationScript:
                    if bytes(contract.ScriptHash.Data) == script.VerificationScript:
                        return True


            #do watch only stuff... not sure yet what it is...
            return False


    def CheckAddressState(self, script_hash):
        for key,contract in self._contracts.items():
            if contract.ScriptHash.ToBytes() == script_hash.ToBytes():
                return AddressState.InWallet
#        for watch in self._watch_only:
#            if watch.ScriptHash == script_hash:
#                return AddressState.WatchOnly
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


    def GetContracts(self):
        return self._contracts


    def MakeTransaction(self, tx, account):

        raise NotImplementedError()



    def ToJson(self):
        #abstract
        pass

