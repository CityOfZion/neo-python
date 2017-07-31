#!/usr/bin/env python

from neo.Wallets.Wallet import Wallet
from neo.Wallets.Coin import Coin as WalletCoin
from neo.Wallets.Contract import Contract as WalletContract
from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.AssetType import *
from enum import Enum

from .PWDatabase import PWDatabase
from .Models import *
from autologging import logged

@logged
class UserWallet(Wallet):

    Version = None

    def __init__(self, path, passwordKey, create):
        super(UserWallet, self).__init__(path, passwordKey=passwordKey, create=create)


    def BuildDatabase(self):
        db = PWDatabase.ContextDB()
        try:
            db.create_tables([Account,Address,Coin,Contract,Key,Transaction,TransactionInfo,])
            self.__log.debug("created tables")
        except Exception as e:
            print("couldn't create tables: %s " % e)

    def DB(self):
        return PWDatabase.Context()


    def AddContract(self, contract):

        super(UserWallet, self).AddContract(contract)

        db_contract = Contract.get(Contract.ScriptHash == contract.ScriptHash)

        if contract is not None:
            db_contract.PublicKeyHash = contract.PublicKeyHash
        else:
            address = Address.get(Address.ScriptHash == Contract.ScriptHash)

            if address is None:
                address = Address.create(ScriptHash = Contract.ScriptHash)
                address.save()

            db_contract = Contract.create(RawData=contract.ToArray(),ScriptHash = contract.ScriptHash, PublicKeyHash = contract.PublicKeyHash)
            db_contract.save()

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
        try:
            return Key.get(Name=key).Value
        except Exception as e:
            print('could not get key %s ' % e)

    def LoadTransactions(self):
        return Transaction.select()

