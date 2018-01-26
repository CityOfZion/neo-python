#!/usr/bin/env python
import binascii

from logzero import logger
from playhouse.migrate import SqliteMigrator, BooleanField, migrate
from .PWDatabase import PWDatabase

from neo.Wallets.Wallet import Wallet
from neo.Wallets.Coin import Coin as WalletCoin
from neo.SmartContract.Contract import Contract as WalletContract
from neo.IO.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.Transaction import Transaction as CoreTransaction
from neocore.KeyPair import KeyPair as WalletKeyPair
from neo.Wallets.NEP5Token import NEP5Token as WalletNEP5Token
from neocore.Cryptography.Crypto import Crypto
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neocore.UInt256 import UInt256
from neo.Wallets.Coin import CoinState
from neo.EventHub import SmartContractEvent, events
from neo.Implementations.Wallets.peewee.Models import Account, Address, Coin, \
    Contract, Key, Transaction, \
    TransactionInfo, NEP5Token, NamedAddress, VINHold
import json


class UserWallet(Wallet):
    Version = None

    __dbaccount = None

    _aliases = None

    _holds = None

    _db = None

    def __init__(self, path, passwordKey, create):

        super(UserWallet, self).__init__(path, passwordKey=passwordKey, create=create)
        logger.debug("initialized user wallet %s " % self)
        self.LoadNamedAddresses()
        self.initialize_holds()

    def initialize_holds(self):
        self.LoadHolds()

        # Handle EventHub events for SmartContract decorators
        @events.on(SmartContractEvent.RUNTIME_NOTIFY)
        def call_on_event(sc_event):
            # Make sure this event is for this specific smart contract
            self.on_notify_sc_event(sc_event)

    def on_notify_sc_event(self, sc_event):
        if not sc_event.test_mode:
            notify_type = sc_event.event_payload[0]
            if type(notify_type) is bytes:
                if notify_type == b'hold_created':
                    self.process_hold_created_event(sc_event.event_payload[1:])
                elif notify_type in [b'hold_cancelled', b'hold_cleaned_up']:
                    self.process_destroy_hold(notify_type, sc_event.event_payload[1])

    def process_hold_created_event(self, payload):
        if len(payload) == 4:
            vin = payload[0]
            from_addr = UInt160(data=payload[1])
            to_addr = UInt160(data=payload[2])
            amount = int.from_bytes(payload[3], 'little')
            v_index = int.from_bytes(vin[32:], 'little')
            v_txid = UInt256(data=vin[0:32])
            if to_addr.ToBytes() in self._contracts.keys() and from_addr in self._watch_only:
                hold, created = VINHold.get_or_create(
                    Index=v_index, Hash=v_txid.ToBytes(), FromAddress=from_addr.ToBytes(), ToAddress=to_addr.ToBytes(), Amount=amount, IsComplete=False
                )
                if created:
                    self.LoadHolds()

    def process_destroy_hold(self, destroy_type, vin_to_cancel):
        completed = self.LoadCompletedHolds()
        for hold in completed:
            if hold.Vin == vin_to_cancel:
                logger.info('[%s] Deleting hold %s' % (destroy_type, json.dumps(hold.ToJson(), indent=4)))
                hold.delete_instance()

    def BuildDatabase(self):
        self._db = PWDatabase(self._path).DB
        try:
            self._db.create_tables([Account, Address, Coin, Contract, Key, NEP5Token, VINHold,
                                    Transaction, TransactionInfo, NamedAddress], safe=True)
        except Exception as e:
            logger.error("Could not build database %s " % e)

    def Migrate(self):
        migrator = SqliteMigrator(self._db)
        migrate(
            migrator.drop_not_null('Contract', 'Account_id'),
            migrator.add_column('Address', 'IsWatchOnly', BooleanField(default=False)),
        )

    def DB(self):
        return self._db

    def Rebuild(self):
        super(UserWallet, self).Rebuild()

        for c in Coin.select():
            c.delete_instance()
        for tx in Transaction.select():
            tx.delete_instance()

        logger.debug("wallet rebuild: deleted coins and transactions %s %s " %
                     (Coin.select().count(), Transaction.select().count()))

    def Close(self):
        if self._db:
            self._db.close()
            self._db = None

    @staticmethod
    def Open(path, password):
        return UserWallet(path=path, passwordKey=password, create=False)

    @staticmethod
    def Create(path, password):
        """
        Create a new user wallet.

        Args:
            path (str): A path indicating where to create or open the wallet i.e. "/Wallets/mywallet".
            password (str): a 10 characters minimum password to secure the wallet with.

        Returns:
             UserWallet: a UserWallet instance.
        """
        wallet = UserWallet(path=path, passwordKey=password, create=True)
        wallet.CreateKey()
        return wallet

    def CreateKey(self, prikey=None):
        """
        Create a KeyPair and store it encrypted in the database.

        Args:
            private_key (iterable_of_ints): (optional) 32 byte private key.

        Returns:
            KeyPair: a KeyPair instance.
        """
        account = super(UserWallet, self).CreateKey(private_key=prikey)
        self.OnCreateAccount(account)
        contract = WalletContract.CreateSignatureContract(account.PublicKey)
        self.AddContract(contract)
        return account

    def OnCreateAccount(self, account):
        """
        Save a KeyPair in encrypted form into the database.

        Args:
            account (KeyPair):
        """
        pubkey = account.PublicKey.encode_point(False)
        pubkeyunhex = binascii.unhexlify(pubkey)
        pub = pubkeyunhex[1:65]

        priv = bytearray(account.PrivateKey)
        decrypted = pub + priv
        encrypted_pk = self.EncryptPrivateKey(bytes(decrypted))

        db_account, created = Account.get_or_create(
            PrivateKeyEncrypted=encrypted_pk, PublicKeyHash=account.PublicKeyHash.ToBytes())
        db_account.save()
        self.__dbaccount = db_account

    def AddContract(self, contract):
        """
        Add a contract to the database.

        Args:
            contract(neo.SmartContract.Contract): a Contract instance.
        """
        super(UserWallet, self).AddContract(contract)

        try:
            db_contract = Contract.get(ScriptHash=contract.ScriptHash.ToBytes())
            db_contract.delete_instance()
        except Exception as e:
            logger.info("contract does not exist yet")

        sh = bytes(contract.ScriptHash.ToArray())
        address, created = Address.get_or_create(ScriptHash=sh)
        address.IsWatchOnly = False
        address.save()
        db_contract = Contract.create(RawData=contract.ToArray(),
                                      ScriptHash=contract.ScriptHash.ToBytes(),
                                      PublicKeyHash=contract.PublicKeyHash.ToBytes(),
                                      Address=address,
                                      Account=self.__dbaccount)

        logger.debug("Creating db contract %s " % db_contract)

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

    def AddNamedAddress(self, script_hash, title):
        script_hash_bytes = bytes(script_hash.ToArray())

        alias, created = NamedAddress.get_or_create(ScriptHash=script_hash_bytes, Title=title)

        self.LoadNamedAddresses()

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
            logger.error("Could not load watch only: %s. You may need to migrate your wallet. Run 'wallet migrate'." % e)

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
            logger.error("could not load coins %s " % e)

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
        logger.debug("Looking for key %s " % key)
        try:
            return Key.get(Name=key).Value
        except Exception as e:
            logger.error("Could not get key %s " % e)

        return None

    def LoadTransactions(self):
        return Transaction.select()

    def LoadNamedAddresses(self):
        self._aliases = NamedAddress.select()

    def LoadHolds(self):
        self._holds = VINHold.filter(IsComplete=False)
        return self._holds

    def LoadCompletedHolds(self):
        return VINHold.filter(IsComplete=True)

    @property
    def NamedAddr(self):
        return self._aliases

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
                logger.debug("saved coin %s " % c)
            except Exception as e:
                logger.error("COULDN'T SAVE!!!! %s " % e)

        for coin in changed:
            for hold in self._holds:
                if hold.Reference == coin.Reference and coin.State & CoinState.Spent > 0:
                    hold.IsComplete = True
                    hold.save()
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.State = coin.State
                c.save()
            except Exception as e:
                logger.error("Coulndn't change coin %s %s (coin to change not found)" % (coin, e))

        for coin in deleted:
            for hold in self._holds:
                if hold.Reference == coin.Reference:
                    hold.IsComplete = True
                    hold.save()
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.delete_instance()

            except Exception as e:
                logger.error("could not delete coin %s %s " % (coin, e))

    @property
    def Addresses(self):
        result = []
        for addr in Address.select():
            #            addr_str = Crypto.ToAddress(UInt160(data=addr.ScriptHash))
            result.append(addr.ToString())

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

    def DeleteNEP5Token(self, token):

        success = super(UserWallet, self).DeleteNEP5Token(token)

        try:
            db_token = NEP5Token.get(ContractHash=token.ScriptHash.ToBytes())
            db_token.delete_instance()
        except Exception as e:
            pass
        return success

    def DeleteAddress(self, script_hash):
        success, coins_toremove = super(UserWallet, self).DeleteAddress(script_hash)

        for coin in coins_toremove:
            try:
                c = Coin.get(TxId=bytes(coin.Reference.PrevHash.Data), Index=coin.Reference.PrevIndex)
                c.delete_instance()
            except Exception as e:
                logger.error("Could not delete coin %s %s " % (coin, e))

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
            logger.info("Script hash %s %s" % (addr.ScriptHash, type(addr.ScriptHash)))
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
                token_balances = self.TokenBalancesForAddress(addr_str)
                script_hash = binascii.hexlify(addr.ScriptHash)
                json = {'address': addr_str, 'script_hash': script_hash.decode('utf8'), 'tokens': token_balances}
                addresses.append(json)

        balances = []
        watch_balances = []
        for asset in assets:
            if type(asset) is UInt256:
                bc_asset = Blockchain.Default().GetAssetState(asset.ToBytes())
                total = self.GetBalance(asset).value / Fixed8.D
                watch_total = self.GetBalance(asset, bool(CoinState.WatchOnly)).value / Fixed8.D
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

        jsn['claims'] = {
            'available': self.GetAvailableClaimTotal().ToString(),
            'unavailable': self.GetUnavailableBonus().ToString()
        }

        alia = NamedAddress.select()
        if len(alia):
            na = {}
            for n in alia:
                na[n.Title] = n.ToString()
            jsn['named_addr'] = na

        if verbose:
            jsn['coins'] = [coin.ToJson() for coin in self.FindUnspentCoins()]
            jsn['transactions'] = [tx.ToJson() for tx in self.GetTransactions()]
        return jsn
