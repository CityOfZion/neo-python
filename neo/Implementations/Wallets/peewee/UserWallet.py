#!/usr/bin/env python

from neo.Wallets.Wallet import Wallet
from neo.Wallets.Coin import Coin as WalletCoin
from neo.SmartContract.Contract import Contract as WalletContract
from neo.IO.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.Transaction import Transaction as CoreTransaction
from neo.Core.State.AssetState import AssetState
from neo.Wallets.KeyPair import KeyPair as WalletKeyPair
from neo.Wallets.NEP5Token import NEP5Token as WalletNEP5Token
from Crypto import Random
from neo.Cryptography.Crypto import Crypto
from neo.UInt160 import UInt160
import binascii
from neo.Fixed8 import Fixed8
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256

from .PWDatabase import PWDatabase

from neo.Implementations.Wallets.peewee.Models import Account, Address, Coin, \
    Contract, Key, Transaction, \
    TransactionInfo, NEP5Token

from autologging import logged
import json
from playhouse.migrate import *
from neo.Wallets.Coin import CoinState


@logged
class UserWallet(Wallet):

    Version = None

    __dbaccount = None

    def __init__(self, path, passwordKey, create):

        super(UserWallet, self).__init__(path, passwordKey=passwordKey, create=create)
        self.__log.debug("initialized user wallet!! %s " % self)

    def BuildDatabase(self):
        PWDatabase.Destroy()
        PWDatabase.Initialize(self._path)
        db = PWDatabase.ContextDB()
        try:
            db.create_tables([Account, Address, Coin, Contract, Key, NEP5Token, Transaction, TransactionInfo, ], safe=True)
        except Exception as e:
            print("Couldnt build database %s " % e)
            self.__log.debug("couldnt build database %s " % e)

    def Migrate(self):
        db = PWDatabase.ContextDB()
        migrator = SqliteMigrator(db)

        migrate(
            migrator.drop_not_null('Contract', 'Account_id'),
            migrator.add_column('Address', 'IsWatchOnly', BooleanField(default=False)),
        )

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
        return UserWallet(path=path, passwordKey=password, create=False)

    @staticmethod
    def Create(path, password):
        wallet = UserWallet(path=path, passwordKey=password, create=True)
        wallet.CreateKey()
        return wallet

    def CreateKey(self, prikey=None):
        if prikey:
            private_key = prikey
        else:
            private_key = bytes(Random.get_random_bytes(32))

        account = WalletKeyPair(priv_key=private_key)
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

        db_account, created = Account.get_or_create(PrivateKeyEncrypted=encrypted_pk, PublicKeyHash=account.PublicKeyHash.ToBytes())
        db_account.PrivateKeyEncrypted = encrypted_pk
        db_account.save()
        self.__dbaccount = db_account

    def AddContract(self, contract):

        super(UserWallet, self).AddContract(contract)

        db_contract = None
        try:
            db_contract = Contract.get(ScriptHash=contract.ScriptHash.ToBytes())
            db_contract.delete_instance()
            db_contract = None
        except Exception as e:
            self.__log.debug("contract does not exist yet")

        if db_contract is not None:
            db_contract.PublicKeyHash = contract.PublicKeyHash.ToBytes()
        else:
            sh = bytes(contract.ScriptHash.ToArray())
            address, created = Address.get_or_create(ScriptHash=sh)
            address.IsWatchOnly = False
            address.save()
            db_contract = Contract.create(RawData=contract.ToArray(),
                                          ScriptHash=contract.ScriptHash.ToBytes(),
                                          PublicKeyHash=contract.PublicKeyHash.ToBytes(),
                                          Address=address,
                                          Account=self.__dbaccount)

            self.__log.debug("Creating db contract %s " % db_contract)

            db_contract.save()

    def AddWatchOnly(self, script_hash):
        super(UserWallet, self).AddWatchOnly(script_hash)

        script_hash_bytes = bytes(script_hash.ToArray())
        address = None

        try:
            address = Address.get(ScriptHash=script_hash_bytes)
        except Exception as e:
            # Address.DoesNotExist
            pass

        if address is None:
            address = Address.create(ScriptHash=script_hash_bytes, IsWatchOnly=True)
            address.save()
            return address
        else:
            raise Exception("Address already exists in wallet")

    def AddNEP5Token(self, token):

        super(UserWallet, self).AddNEP5Token(token)

        try:
            db_token = NEP5Token.get(ContractHash=token.ScriptHash.ToBytes())
            db_token.delete_instance()
        except Exception as e:
            pass

        db_token = NEP5Token.create(
            ContractHash=token.ScriptHash.ToBytes(),
            Name=token.name,
            Symbol=token.symbol,
            Decimals=token.decimals
        )
        db_token.save()
        return True

    def FindUnspentCoins(self, from_addr=None, use_standard=False, watch_only_val=0):
        return super(UserWallet, self).FindUnspentCoins(from_addr, use_standard, watch_only_val=watch_only_val)

    def GetTransactions(self):
        transactions = []
        for db_tx in Transaction.select():
            raw = binascii.unhexlify(db_tx.RawData)
            tx = CoreTransaction.DeserializeFromBufer(raw, 0)
            transactions.append(tx)
        return transactions

    def LoadWatchOnly(self):
        items = []

        try:
            for addr in Address.select():
                if addr.IsWatchOnly:
                    watchOnly = UInt160(data=addr.ScriptHash)
                    items.append(watchOnly)

            return items

        except Exception as e:
            print("couldnt load watch only : %s " % e)
            print("You may need to migrate your wallet. Run 'wallet migrate'.")

        return []

    def LoadCoins(self):

        coins = {}

        try:
            for coin in Coin.select():
                reference = CoinReference(prev_hash=UInt256(coin.TxId), prev_index=coin.Index)
                output = TransactionOutput(UInt256(coin.AssetId), Fixed8(coin.Value), UInt160(coin.ScriptHash))
                walletcoin = WalletCoin.CoinFromRef(reference, output, coin.State)
                coins[reference] = walletcoin
        except Exception as e:
            print("could not load coins %s " % e)

        return coins

    def LoadContracts(self):

        ctr = {}

        for ct in Contract.select():

            data = binascii.unhexlify(ct.RawData)
            contract = Helper.AsSerializableWithType(data, 'neo.SmartContract.Contract.Contract')
            ctr[contract.ScriptHash.ToBytes()] = contract

        return ctr

    def LoadKeyPairs(self):
        keypairs = {}
        for db_account in Account.select():
            encrypted = db_account.PrivateKeyEncrypted
            decrypted = self.DecryptPrivateKey(encrypted)
            acct = WalletKeyPair(decrypted)

            assert acct.PublicKeyHash.ToString() == db_account.PublicKeyHash

            keypairs[acct.PublicKeyHash.ToBytes()] = acct

        return keypairs

    def LoadNEP5Tokens(self):
        tokens = {}

        for db_token in NEP5Token.select():
            token = WalletNEP5Token.FromDBInstance(db_token)
            tokens[token.ScriptHash.ToBytes()] = token

        return tokens

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
            k = Key.create(Name=key, Value=value)

        k.save()

    def OnProcessNewBlock(self, block, added, changed, deleted):

        for tx in block.FullTransactions:

            if self.IsWalletTransaction(tx):
                db_tx = None
                try:
                    db_tx = Transaction.get(Hash=tx.Hash.ToBytes())
                except Exception as e:
                    pass

                ttype = tx.Type
                if type(ttype) is bytes:
                    ttype = int.from_bytes(tx.Type, 'little')

                if not db_tx:
                    db_tx = Transaction.create(
                        Hash=tx.Hash.ToBytes(),
                        TransactionType=ttype,
                        RawData=tx.ToArray(),
                        Height=block.Index,
                        DateTime=block.Timestamp
                    )
                else:
                    db_tx.Height = block.Index

                db_tx.save()

        self.OnCoinsChanged(added, changed, deleted)

    def OnSaveTransaction(self, tx, added, changed, deleted):

        self.OnCoinsChanged(added, changed, deleted)

    def OnCoinsChanged(self, added, changed, deleted):

        for coin in added:
            addr_hash = bytes(coin.Output.ScriptHash.Data)

            try:
                address = Address.get(ScriptHash=addr_hash)

                c = Coin(
                    TxId=bytes(coin.Reference.PrevHash.Data),
                    Index=coin.Reference.PrevIndex,
                    AssetId=bytes(coin.Output.AssetId.Data),
                    Value=coin.Output.Value.value,
                    ScriptHash=bytes(coin.Output.ScriptHash.Data),
                    State=coin.State,
                    Address=address
                )
                c.save()
                self.__log.debug("saved coin %s " % c)
            except Exception as e:
                print("COLUDNT SAVE!!!! %s " % e)

        for coin in changed:
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.State = coin.State
                c.save()
            except Exception as e:
                print("Coulndnt change coin %s %s" % (coin, e))
                self.__log.debug("coin to change not found! %s %s " % (coin, e))

        for coin in deleted:
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.delete_instance()

            except Exception as e:
                print("Couldnt delete coin %s %s " % (e, coin))
                self.__log.debug("could not delete coin %s %s " % (coin, e))

    @property
    def Addresses(self):
        result = []
        for addr in Address.select():
            addr_str = Crypto.ToAddress(UInt160(data=addr.ScriptHash))
            result.append(addr_str)

        return result

    def TokenBalancesForAddress(self, address):
        if len(self._tokens):
            jsn = []
            tokens = list(self._tokens.values())
            for t in tokens:
                jsn.append(
                    '[%s] %s : %s' % (t.ScriptHash.ToString(), t.symbol, t.GetBalance(self, address, as_string=True))
                )
            return jsn

        return None

    def PubKeys(self):
        keys = self.LoadKeyPairs()
        jsn = []
        for k in keys.values():
            pub = k.PublicKey.encode_point(True)
            for ct in self._contracts.values():
                if ct.PublicKeyHash == k.PublicKeyHash:
                    addr = ct.Address
                    jsn.append({'Address': addr, 'Public Key': pub.decode('utf-8')})

        return jsn

    def DeleteAddress(self, script_hash):

        success, coins_toremove = super(UserWallet, self).DeleteAddress(script_hash)

        for coin in coins_toremove:
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.delete_instance()
            except Exception as e:
                print("Couldnt delete coin %s %s " % (e, coin))
                self.__log.debug("could not delete coin %s %s " % (coin, e))

        todelete = bytes(script_hash.ToArray())

        for c in Contract.select():

            address = c.Address
            if address.ScriptHash == todelete:

                c.delete_instance()
                address.delete_instance()

        try:
            address = Address.get(ScriptHash=todelete)
            address.delete_instance()
        except Exception as e:
            pass

        return True, coins_toremove

    def ToJson(self, verbose=False):

        assets = self.GetCoinAssets()
        tokens = list(self._tokens.values())
        assets = assets + tokens

        if Blockchain.Default().Height == 0:
            percent_synced = 0
        else:
            percent_synced = int(100 * self._current_height / Blockchain.Default().Height)

        jsn = {}
        jsn['path'] = self._path

        addresses = []
        has_watch_addr = False
        for addr in Address.select():
            #            print("Script hash %s %s" % (addr.ScriptHash, type(addr.ScriptHash)))
            addr_str = Crypto.ToAddress(UInt160(data=addr.ScriptHash))
            acct = Blockchain.Default().GetAccountState(addr_str)
            token_balances = self.TokenBalancesForAddress(addr_str)
            if acct:
                json = acct.ToJson()
                json['is_watch_only'] = addr.IsWatchOnly
                addresses.append(json)
                if token_balances:
                    json['tokens'] = token_balances
                if addr.IsWatchOnly:
                    has_watch_addr = True
            else:
                addresses.append(addr_str)

        balances = []
        watch_balances = []
        for asset in assets:
            if type(asset) is UInt256:
                bc_asset = Blockchain.Default().GetAssetState(asset.ToBytes())
                total = self.GetBalance(asset).value / Fixed8.D
                watch_total = self.GetBalance(asset, CoinState.WatchOnly).value / Fixed8.D
                balances.append("[%s]: %s " % (bc_asset.GetName(), total))
                watch_balances.append("[%s]: %s " % (bc_asset.GetName(), watch_total))
            elif type(asset) is WalletNEP5Token:
                balances.append("[%s]: %s " % (asset.symbol, self.GetBalance(asset)))
                watch_balances.append("[%s]: %s " % (asset.symbol, self.GetBalance(asset, True)))

        tokens = []
        for t in self._tokens.values():
            tokens.append(t.ToJson())

        jsn['addresses'] = addresses
        jsn['height'] = self._current_height
        jsn['percent_synced'] = percent_synced
        jsn['synced_balances'] = balances

        if has_watch_addr:
            jsn['synced_watch_only_balances'] = watch_balances

        jsn['public_keys'] = self.PubKeys()
        jsn['tokens'] = tokens
        if verbose:
            jsn['coins'] = [coin.ToJson() for coin in self.FindUnspentCoins()]
            jsn['transactions'] = [tx.ToJson() for tx in self.GetTransactions()]
        return jsn
