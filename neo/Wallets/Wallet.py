# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from neo.Wallets.Wallet import Wallet
"""

from neo.Core.TX.Transaction import TransactionType,TransactionOutput
from neo.Core.State.CoinState import CoinState
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Cryptography.Helper import *
from neo.Cryptography.Crypto import Crypto
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
from neo.Fixed8 import Fixed8
from neo.UInt160 import UInt160
from itertools import groupby
from base58 import b58decode
from neo.Core.Helper import Helper
from Crypto import Random
from Crypto.Cipher import AES
import pdb
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

            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            master = AES.new(passwordHash, AES.MODE_CBC, self._iv)
            mk = master.encrypt(self._master_key)
            self.SaveStoredData('PasswordHash', passwordHash)
            self.SaveStoredData('IV', self._iv),
            self.SaveStoredData('MasterKey', mk)
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
            master_stored = self.LoadStoredData('MasterKey')
            aes = AES.new(hkey.digest(),AES.MODE_CBC,self._iv)
            self._master_key = aes.decrypt(master_stored)

            self._keys = self.LoadKeyPairs()
            self._contracts = self.LoadContracts()
            self._watch_only = self.LoadWatchOnly()
            self._coins = self.LoadCoins()
            try:
                h = int(self.LoadStoredData('Height'))
                self._current_height = h
            except Exception as e:
                print("couldnt load height data %s " % e)
                self._current_height = 0

#            self._current_height = 470000

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
        return self.ContainsKeyHash(Crypto.ToScriptHash(public_key.encode_point(True),unhex=False))

    def ContainsKeyHash(self, public_key_hash):

        return public_key_hash.ToBytes() in self._keys.keys()

    def ContainsAddress(self, script_hash):
        return self.CheckAddressState(script_hash) >= AddressState.InWallet

    def ContainsAddressStr(self, address):
        for key,contract in self._contracts.items():
            if contract.Address == address:
                return True
        return False


    def CreateKey(self):
        private_key = bytes(Random.get_random_bytes(32))
#        self.__log.debug("private key %s " % private_key)

        key = KeyPair(priv_key = private_key)
        self._keys[key.PublicKeyHash.ToBytes()] = key
        self.__log.debug("keys %s " % self._keys.items())
        return key


    def EncryptPrivateKey(self, decrypted):
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)
        return aes.encrypt(decrypted)

    def DecryptPrivateKey(self, encrypted_private_key):
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)
        return aes.decrypt(encrypted_private_key)

    def DeleteKey(self, public_key_hash):
        raise NotImplementedError()

    def DeleteAddress(self, script_hash):
        coin_keys_toremove = []
        coins_to_remove = []
        for key, coinref in self._coins.items():
            if coinref.Output.ScriptHash.ToBytes() == script_hash.ToBytes():
                coin_keys_toremove.append(key)
                coins_to_remove.append(coinref)

        for k in coin_keys_toremove:
            del self._coins[k]

        ok = False
        if script_hash.ToBytes() in self._contracts.keys():
            ok=True
            del self._contracts[script_hash.ToBytes()]
        elif script_hash.ToBytes() in self._watch_only.keys():
            ok=True
            del self._contracts[script_hash.ToBytes()]

        return ok, coins_to_remove

    def FindUnspentCoins(self):

        ret=[]
        for coin in self.GetCoins():
            if coin.State & CoinState.Confirmed > 0 and \
                coin.State & CoinState.Spent == 0 and \
                coin.State & CoinState.Locked == 0 and \
                coin.State & CoinState.Frozen == 0 and \
                coin.State & CoinState.WatchOnly == 0:

                ret.append(coin)

        return ret

    def FindUnspentCoinsByAsset(self, asset_id):
        coins = self.FindUnspentCoins()

        return [coin for coin in coins if coin.Output.AssetId == asset_id]

    def FindUnspentCoinsByAssetAndTotal(self, asset_id, amount):

        coins = self.FindUnspentCoinsByAsset(asset_id)

        sum = Fixed8(0)

        for coin in coins:
            sum = sum + coin.Output.Value

        if sum < amount:
            return None

        sorted(coins, key=lambda coin: coin.Output.Value.value)

        total = Fixed8(0)

        for index,coin in enumerate(coins):
            total = total + coin.Output.Value
            if total >= amount:
                return coins[0:index+1]



    def GetKey(self, public_key_hash):
        if public_key_hash.ToBytes() in self._keys.keys():
            return self._keys[public_key_hash.ToBytes()]
        return None

    def GetKeyByScriptHash(self, script_hash):

        contract = self.GetContract(script_hash)
        if contract:
            return self.GetKey(contract.PublicKeyHash)
        return None


    def GetAvailable(self, asset_id):
        raise NotImplementedError()

    def GetBalance(self, asset_id):
        total=Fixed8(0)
        for coin in self.GetCoins():
            if coin.Output.AssetId == asset_id:

                if coin.State & CoinState.Confirmed > 0 and \
                    coin.State & CoinState.Spent == 0 and \
                    coin.State & CoinState.Locked == 0 and \
                    coin.State & CoinState.Frozen == 0 and \
                    coin.State & CoinState.WatchOnly == 0:

                    total = total + coin.Output.Value

        return total



    def SaveStoredData(self, key, value):
        # abstract
        pass

    def LoadStoredData(self, key):
        # abstract
        pass

    def LoadKeyPairs(self):
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

        self.SaveStoredData("Height", self._current_height)
        self.__log.debug("Wallet processed block to %s " % self._current_height)
#        end = time.clock()

    def ProcessNewBlock(self, block):

        added = set()
        changed = set()
        deleted = set()


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

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])


    def ValidatePassword(self, password):

        return hashlib.sha256(password.encode('utf-8')).digest() == self.LoadStoredData('PasswordHash')



    def GetChangeAddress(self):
        for contract in self._contracts.values():
            if contract.IsStandard:
                return contract.ScriptHash

        if len(self._contracts.values()):
            return self._contracts.values()[0]

        raise Exception("Could not find change address")

    def GetDefaultContract(self):
        try:
            return self.GetContracts()[0]
        except Exception as e:
            print("NO CONTRACTS!")
        return None

    def GetKeys(self):
        return [key for key in self._keys.values()]

    def GetCoinAssets(self):
        assets = set()
        for coin in self.GetCoins():
            assets.add(coin.Output.AssetId)
        return list(assets)

    def GetCoins(self):
        return [coin for coin in self._coins.values()]

    def GetContract(self, script_hash):
        if script_hash.ToBytes() in self._contracts.keys():
            return self._contracts[script_hash.ToBytes()]
        return None

    def GetContracts(self):
        return [contract for contract in self._contracts.values()]
#        return self._contracts


    def MakeTransaction(self, tx, change_address = None, fee = Fixed8(0)):

        tx.ResetReferences()

        if not tx.outputs: tx.outputs = []
        if not tx.inputs: tx.inputs = []

        fee = fee + tx.SystemFee()

        paytotal = {}
        if tx.Type != int.from_bytes( TransactionType.IssueTransaction, 'little'):

            for key, group in groupby(tx.outputs, lambda x: x.AssetId):
                sum = Fixed8(0)
                for item in group:
                    sum = sum + item.Value
                paytotal[key] = sum
        else:
            paytotal = {}

        if fee > Fixed8.Zero():

            if Blockchain.SystemCoin().Hash in paytotal.keys():
                paytotal[Blockchain.SystemCoin().Hash] = paytotal[Blockchain.SystemCoin().Hash] + fee
            else:
                paytotal[Blockchain.SystemCoin().Hash] = fee

        paycoins = {}


        for assetId,amount in paytotal.items():
            paycoins[assetId] = self.FindUnspentCoinsByAssetAndTotal(assetId, amount)


        for key,unspents in paycoins.items():
            if unspents == None:
                print("insufficient funds for asset id: %s " % key)
                return None

        input_sums = {}

        for assetId,unspents in paycoins.items():
            sum=Fixed8(0)
            for coin in unspents:
                sum = sum + coin.Output.Value
            input_sums[assetId] = sum

        if not change_address:
            change_address = self.GetChangeAddress()

        new_outputs = []

        for assetId,sum in input_sums.items():
            if sum > paytotal[assetId]:
                difference = sum - paytotal[assetId]
                output = TransactionOutput(AssetId=assetId,Value=difference,script_hash=change_address)
                new_outputs.append(output)


        inputs = []

        for item in paycoins.values():
            for ref in item:
                inputs.append(ref.Reference)


        tx.inputs = inputs
        tx.outputs = tx.outputs + new_outputs

        return tx


    def SaveTransaction(self, tx):
#        changes = set()

#        for input in tx.inputs:
#            if self input in self._coins.
#        print("wallet SaveTransaction not impletmented yet")
        pass

    def Sign(self, context):
        success = False

        for hash in context.ScriptHashes:

            contract = self.GetContract(hash)
            if contract is None:
                continue

            key = self.GetKeyByScriptHash(hash)

            if key is None:
                continue

            signature = Helper.Sign(context.Verifiable, key)

            res = context.AddSignature(contract, key.PublicKey, signature)

            success |=res

        return success


    def ToJson(self, verbose=False):
        #abstract
        pass

