#!/usr/bin/env python

from neo.Wallets.Wallet import Wallet
from neo.Wallets.Coin import Coin as WalletCoin
from neo.SmartContract.Contract import Contract as WalletContract
from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from neo.IO.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.Transaction import Transaction as CoreTransaction

from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from Crypto import Random
from neo.Cryptography.Crypto import Crypto
import os
from neo.UInt160 import UInt160
import binascii
import pdb
from neo.Fixed8 import Fixed8
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256

from .PWDatabase import PWDatabase

from neo.Implementations.Wallets.peewee.Models import Account, Address, Coin, Contract, Key, Transaction, \
    TransactionInfo

from autologging import logged

@logged
class UserWallet(Wallet):


    Version = None

    __dbaccount = None

    def __init__(self, path, passwordKey, create):

        super(UserWallet, self).__init__(path, passwordKey=passwordKey, create=create)
        self.__log.debug("initialized user wallet!! %s " % self)

    def BuildDatabase(self):
        self.__log.debug("trying to build database!! %s " % self._path)
        PWDatabase.Initialize(self._path)
        db = PWDatabase.ContextDB()
        self.__log.debug("DB %s  " % db)
        try:
            db.create_tables([Account,Address,Coin,Contract,Key,Transaction,TransactionInfo,], safe=True)
            self.__log.debug("created tables!")
        except Exception as e:
            self.__log.debug("couldnt build database %s " % e)

    def DB(self):
        return PWDatabase.Context()

    def Rebuild(self):
        super(UserWallet, self).Rebuild()

        for c in Coin.select():
            c.delete_instance()
        for tx in Transaction.select():
            tx.delete_instance()

        self.__log.debug("deleted coins and transactions %s %s " % (Coin.select().count(), Transaction.select().count()))

    @staticmethod
    def Open(path, password):
        return UserWallet(path=path, passwordKey=password,create=False)


    @staticmethod
    def Create(path, password):
        wallet = UserWallet(path=path, passwordKey=password,create=True)
        wallet.CreateKey()
        return wallet


    def CreateKey(self):
        private_key = bytes(Random.get_random_bytes(32))
        print("CREATING PRIVATE KEY  %s " % private_key)
        self.__log.debug("user wallet private key %s " % private_key)

        account = WalletKeyPair(priv_key=private_key)
        print("ACCOUNT PUBKEY %s " % account.PublicKey)
        print("ACCOUNT PUBKEY ENCODE" % account.PublicKey.encode_point(True))
        print("ACCOUNT PUBKEY HASH: %s " % account.PublicKeyHash.ToBytes())
        self.__log.debug("User wallet public key %s " % account.PublicKey)
        self._keys[account.PublicKeyHash.ToBytes()] = account

        self.OnCreateAccount(account)
        contract = WalletContract.CreateSignatureContract(account.PublicKey)
        self.AddContract(contract)
        return account



    def OnCreateAccount(self, account):

        pubkey = account.PublicKey.encode_point(False)
        pubkeyunhex = binascii.unhexlify(pubkey)
        pub = pubkeyunhex[1:65]

        priv = bytearray(account.PrivateKey)
        decrypted = pub + priv
        encrypted_pk = self.EncryptPrivateKey(bytes(decrypted))

        db_account,created = Account.get_or_create(PrivateKeyEncrypted=encrypted_pk, PublicKeyHash= account.PublicKeyHash.ToBytes())
        db_account.PrivateKeyEncrypted = encrypted_pk
        db_account.save()
        self.__dbaccount = db_account

    def AddContract(self, contract):

        super(UserWallet, self).AddContract(contract)

        db_contract = None
        try:
            db_contract = Contract.get(ScriptHash = contract.ScriptHash.ToBytes())
        except Exception as e:
            self.__log.debug("contract does not exist yet")

        if db_contract is not None:
            db_contract.PublicKeyHash = contract.PublicKeyHash.ToBytes()
        else:
            sh = bytes(contract.ScriptHash.ToArray())
            self.__log.debug("saving address %s " % sh)
            address, created = Address.get_or_create(ScriptHash = sh)
            address.save()
            self.__log.debug("created address ? %s %s " % (address, created))
            db_contract = Contract.create(RawData=contract.ToArray(),
                                          ScriptHash = contract.ScriptHash.ToBytes(),
                                          PublicKeyHash = contract.PublicKeyHash.ToBytes(),
                                          Address=address,
                                          Account=self.__dbaccount)

            self.__log.debug("Creating db contract %s " % db_contract)

            db_contract.save()
            self.__log.debug("Created db contract...")

    def AddWatchOnly(self, script_hash):
        super(UserWallet,self).AddWatchOnly(script_hash)

        address = Address.get(ScriptHash = script_hash)

        if address is None:
            address = Address.create(ScriptHash=script_hash)
            address.save()


    def FindUnspentCoins(self):
        return super(UserWallet,self).FindUnspentCoins()

    def GetTransactions(self):
        transactions = []
        for db_tx in Transaction.select():
            raw = binascii.unhexlify( db_tx.RawData )
            tx = CoreTransaction.DeserializeFromBufer(raw,0)
            transactions.append(tx)
        return transactions

    def LoadCoins(self):

        coins ={}

        try:
            for coin in Coin.select():
                reference = CoinReference(prev_hash=UInt256(coin.TxId), prev_index=coin.Index)
                output = TransactionOutput(UInt256(coin.AssetId), Fixed8(coin.Value), UInt160(coin.ScriptHash))
                walletcoin = WalletCoin.CoinFromRef(reference,output, coin.State)
                coins[reference] = walletcoin
        except Exception as e:
            print("could not load coins %s " % e)

        return coins


    def LoadContracts(self):

        ctr = {}

        for ct in Contract.select():

            data = binascii.unhexlify( ct.RawData)
            contract = Helper.AsSerializableWithType(data, 'neo.SmartContract.Contract.Contract')
#            pdb.set_trace()
            ctr[contract.ScriptHash.ToBytes()] = contract

        return ctr

    def LoadKeyPairs(self):
        accts=[]
        for db_account in Account.select():
            encrypted = db_account.PrivateKeyEncrypted
            decrypted = self.DecryptPrivateKey(encrypted)
            acct = WalletKeyPair(decrypted)
            assert acct.PublicKeyHash.ToString() == db_account.PublicKeyHash
            accts.append(acct)

        return accts

    def LoadStoredData(self, key):
        self.__log.debug("Looking for key %s " % key)
        try:
            return Key.get(Name=key).Value
        except Exception as e:
            self.__log.debug("Could not get key %s " % e)

        return None

    def LoadTransactions(self):
        return Transaction.select()


    def SaveStoredData(self, key, value):

        k = None
        try:
            k = Key.get(Name=key)
            k.Value = value
        except Exception as e:
            pass

        if k is None:
            k = Key.create(Name=key,Value=value)

        k.save()


    def OnProcessNewBlock(self, block, added, changed, deleted):

#        self.__log.debug("on process new block %s %s %s %s " % (block,added,changed,deleted))

        changed = set()

        for tx in block.FullTransactions:
            if self.IsWalletTransaction(tx):
                db_tx = None
                try:
                    db_tx = Transaction.get(Hash=tx.Hash.ToBytes())
                except Exception as e:
                    pass

                if not db_tx:
                    db_tx = Transaction.create(
                        Hash=tx.Hash.ToBytes(),
                        TransactionType=tx.Type,
                        RawData = tx.ToArray(),
                        Height = block.Index,
                        DateTime = block.Timestamp
                    )
                else:
                    db_tx.Height = block.Index

                db_tx.save()

        self.OnCoinsChanged(added,changed,deleted)


        # @TODO more stuff dealiing with transactions here...


    def OnCoinsChanged(self, added, changed, deleted):


        for coin in added:
            self.__log.debug("on coins changed!-- all addresses:")
            [self.__log.debug('hash: %s %s' % (addr.ScriptHash,type(addr.ScriptHash))) for addr in Address.select()]

            self.__log.debug("output script hash %s %s %s %s" % (coin.Output.ScriptHash, coin.Output.ScriptHash.Data, coin.Output.ScriptHash.ToBytes(),coin.Output.ScriptHash.ToString()))
            addr_hash = bytes(coin.Output.ScriptHash.Data)
            self.__log.debug("addr hash: %s %s " % (addr_hash, type(addr_hash)))
            address = Address.get(ScriptHash=addr_hash)
            self.__log.debug("got address %s " % address)

            c = Coin(
                TxId = bytes(coin.Reference.PrevHash.Data),
                Index = coin.Reference.PrevIndex,
                AssetId = bytes(coin.Output.AssetId.Data),
                Value = coin.Output.Value.value,
                ScriptHash = bytes(coin.Output.ScriptHash.Data),
                State = coin.State,
                Address= address
            )
            self.__log.debug("created coin %s " % c)
            c.save()
            self.__log.debug("saved coin %s " % c)

        for coin in changed:
            try:
                c = Coin.get(TxId = bytes(coin.Reference.PrevHash.Data))
                c.State = coin.State
                c.save()
            except Exception as e:
                self.__log.debug("coin to change not found! %s %s " % (coin,e))

        for coin in deleted:
            try:
                c = Coin.get(TxId = bytes(coin.Reference.PrevHash.Data))
                c.delete()
            except Exception as e:
                self.__log.debug("could not delete coin %s %s " % (coin, e))


    def ToJson(self):

        assets = self.GetCoinAssets()

        jsn = {}
        jsn['path'] = self._path

        addresses = [Crypto.ToAddress(UInt160(data=addr.ScriptHash)) for addr in Address.select()]
        jsn['addresses'] = addresses
        jsn['height'] = self._current_height
        jsn['percent_synced'] = int(100 * self._current_height / Blockchain.Default().Height)
        jsn['coins'] = [ coin.ToJson() for coin in self.FindUnspentCoins()]
#        jsn['transactions'] = [tx.ToJson() for tx in self.GetTransactions()]
        jsn['balances'] = [ "%s -> %s " % (asset.ToString(), self.GetBalance(asset).value / Fixed8.D) for asset in assets]

        return jsn

