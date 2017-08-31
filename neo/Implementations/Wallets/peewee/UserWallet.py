#!/usr/bin/env python

from neo.Wallets.Wallet import Wallet
from neo.Wallets.Coin import Coin as WalletCoin
from neo.SmartContract.Contract import Contract as WalletContract
from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.AssetType import *
from enum import Enum
import random
from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from Crypto import Random
from neo.Cryptography.Crypto import Crypto
import os
from neo.UInt160 import UInt160
import binascii

from .PWDatabase import PWDatabase

from neo.Implementations.Wallets.peewee.Models import Account, Address, Coin, Contract, Key, Transaction, \
    TransactionInfo

from autologging import logged

@logged
class UserWallet(Wallet):



    Version = None

    def __init__(self, path, passwordKey, create):

        super(UserWallet, self).__init__(path, passwordKey=passwordKey, create=create)
        print("initialized user wallet!! %s " % self)

    def BuildDatabase(self):
        print("trying to build database!! %s " % self._path)
        PWDatabase.Initialize(self._path)
        db = PWDatabase.ContextDB()
        print("DB %s  " % db)
        try:
            db.create_tables([Account,Address,Coin,Contract,Key,Transaction,TransactionInfo,], safe=True)
            print("created tables!")
        except Exception as e:
            print("couldnt build database %s " % e)

    def DB(self):
        return PWDatabase.Context()

    @staticmethod
    def Open(path, password):
        print("OPENING WITH PATH %s " % path)
        return UserWallet(path=path, passwordKey=password,create=False)


    @staticmethod
    def Create(path, password):
        wallet = UserWallet(path=path, passwordKey=password,create=True)
        wallet.CreateKey()
        return wallet

    def CreateKey(self):
        private_key = bytes(Random.get_random_bytes(32))
        print("user wallet private key %s " % private_key)

        account = WalletKeyPair(priv_key=private_key)
        print("User wallet public key %s " % account.PublicKey)
        self._keys[account.PublicKeyHash.ToBytes()] = account

        self.OnCreateAccount(account)
        contract = WalletContract.CreateSignatureContract(account.PublicKey)
        self.AddContract(contract)
        return account


#        self._keys[key.PublicKeyHash] = key
 #       print("keys %s " % self._keys.items())
 #       return key

    #       return private_ke


    def OnCreateAccount(self, account):

#        decrypted = bytearray(96)


        pub = bytearray(account.PublicKey.encode_point(False)[1:])[:64]
        print("pub %s "  % pub)
        priv = bytearray(account.PrivateKey)
        print("priv %s " % priv)

        decrypted = pub + priv

        print("decrypeted %s %s " % (decrypted, len(decrypted)))

        encrypted_pk = self.EncryptPrivateKey(bytes(decrypted))
        print("encripted pk %s " % encrypted_pk)

        db_account,created = Account.get_or_create(PrivateKeyEncrypted=encrypted_pk, PublicKeyHash= account.PublicKeyHash.ToBytes())
        db_account.PrivateKeyEncrypted = encrypted_pk
        db_account.save()
        print("DB ACCOUNT %s " % db_account)

    def AddContract(self, contract):

        super(UserWallet, self).AddContract(contract)

        db_contract = None
        try:
            db_contract = Contract.get(ScriptHash = contract.ScriptHash.ToBytes())
        except Exception as e:
            print("contract does not exist yet")

        if db_contract is not None:
            db_contract.PublicKeyHash = contract.PublicKeyHash.ToBytes()
        else:
            sh = bytes(contract.ScriptHash.ToArray())
            print("saving address %s " % sh)
            address, created = Address.get_or_create(ScriptHash = sh)
            address.save()

            print("created address ? %s %s " % (address, created))

            db_contract = Contract.create(RawData=contract.ToArray(),
                                          ScriptHash = contract.ScriptHash.ToBytes(),
                                          PublicKeyHash = contract.PublicKeyHash.ToBytes())

            print("Creating db contract %s " % db_contract)

            db_contract.save()
            print("Created db contract...")

    def AddWatchOnly(self, script_hash):
        super(UserWallet,self).AddWatchOnly(script_hash)

        address = Address.get(ScriptHash = script_hash)

        if address is None:
            address = Address.create(ScriptHash=script_hash)
            address.save()


    def FindUnspentCoins(self):
        super(UserWallet,self).FindUnspentCoins()

    def GetTransactions(self):
        return Transaction.select()

    def LoadCoins(self):

        coins =[]

        for coin in Coin.select():
            reference = CoinReference(prev_hash=coin.TxId, prev_index=coin.Index)
            output = TransactionOutput(coin.AssetId, coin.Value, coin.ScriptHash)
            walletcoin = WalletCoin.CoinFromRef(reference,output, coin.State)
            coins.append(walletcoin)

        return coins


    def LoadContracts(self):
        return Contract.select()

    def LoadStoredData(self, key):
        print("Looking for key %s " % key)
        print("keys count %s " % Key.select().count())
        for k in Key.select():
            print("key is %s " % k)
        try:
            return Key.get(Name=key).Value
        except Exception as e:
            print("Could not get key %s " % e)
            self.__log.debug('could not get key %s ' % e)
        return None

    def LoadTransactions(self):
        return Transaction.select()


    def SaveStoredData(self, key, value):
        print("saving stored data %s %s " % ( key, value))
        keyval, created = Key.get_or_create(Name=key, Value=value)
        keyval.Value = value
        print("keyval %s %s " % (keyval.Name, keyval.Value))
        keyval.save()
        print("saved stored data %s " % keyval)


    def OnProcessNewBlock(self, block, added, changed, deleted):

        print("on process new block %s %s %s %s " % (block,added,changed,deleted))

    def ToJson(self):

        jsn = {}
        jsn['path'] = self._path

        [print("ITEM %s %s" % (type(addr.ScriptHash),addr.ScriptHash)) for addr in Address.select()]

#        addresses = [UInt160(data=addr.ScriptHash) for addr in Address.select()]
#        print("addresses! %s " % addresses)
        addresses = [Crypto.ToAddress(UInt160(data=addr.ScriptHash)) for addr in Address.select()]
        print("addddddresses s %s " % addresses)
#        jsn['addresses'] = [Crypto.ToAddress( addr.ScriptHash for addr in Address.select()]
        jsn['addresses'] = addresses
        return jsn

#        path = self._path

#        print("Saved at %s " % path)

#        addresses = Address.select()
#        for addr in addresses:
#            print("Address: %s " % addr)

