from peewee import Model, CharField, BooleanField, ForeignKeyField, IntegerField, DateTimeField, BlobField, AutoField
from .PWDatabase import PWDatabase
from neocore.Cryptography.Crypto import Crypto
from neocore.UInt256 import UInt256
from neocore.UInt160 import UInt160
import binascii
from neo.Wallets.Coin import CoinReference
from neo.Blockchain import GetBlockchain


class ModelBase(Model):
    class Meta:
        database = PWDatabase.DBProxy()


class Account(ModelBase):
    Id = AutoField()
    PrivateKeyEncrypted = BlobField(unique=True)
    PublicKeyHash = CharField()


class Address(ModelBase):
    Id = AutoField()
    ScriptHash = BlobField(unique=True)
    IsWatchOnly = BooleanField(default=False)

    def ToString(self):
        return Crypto.ToAddress(UInt160(data=self.ScriptHash))


class NamedAddress(ModelBase):
    Id = AutoField()
    ScriptHash = BlobField(unique=True)
    Title = CharField()

    def UInt160ScriptHash(self):
        return UInt160(data=self.ScriptHash)

    def ToString(self):
        return Crypto.ToAddress(UInt160(data=self.ScriptHash))


class Coin(ModelBase):
    Id = AutoField()
    TxId = BlobField()
    Index = IntegerField()
    AssetId = BlobField()
    Value = IntegerField()
    ScriptHash = BlobField()
    State = IntegerField()
    Address = ForeignKeyField(Address)


class Contract(ModelBase):
    Id = AutoField()
    RawData = CharField()
    ScriptHash = BlobField()
    PublicKeyHash = CharField()
    Account = ForeignKeyField(Account, null=True)
    Address = ForeignKeyField(Address)


class Key(ModelBase):
    Id = AutoField()
    Name = CharField(unique=True)
    Value = BlobField()


class NEP5Token(ModelBase):
    ContractHash = CharField(unique=True)
    Name = CharField()
    Symbol = CharField()
    Decimals = IntegerField()


class Transaction(ModelBase):
    Id = AutoField()
    Hash = CharField(unique=True)
    TransactionType = IntegerField()
    RawData = CharField()
    Height = IntegerField()
    DateTime = DateTimeField()


class TransactionInfo(ModelBase):
    Id = AutoField()
    CoreTransaction = ForeignKeyField(Transaction)
    Height = IntegerField()
    DateTime = DateTimeField()


class VINHold(ModelBase):
    Id = AutoField()
    Index = IntegerField()
    Hash = CharField()
    FromAddress = CharField()
    ToAddress = CharField()
    Amount = IntegerField()
    IsComplete = BooleanField(default=False)

    @property
    def Reference(self):
        reference = CoinReference(prev_hash=self.TXHash, prev_index=self.Index)
        return reference

    @property
    def TXHash(self):
        data = bytearray(binascii.unhexlify(self.Hash.encode('utf-8')))
        data.reverse()
        return UInt256(data=data)

    @property
    def Vin(self):
        index = bytearray(self.Index.to_bytes(1, 'little'))
        return self.TXHash.Data + index

    @property
    def OutputHash(self):
        data = bytearray(binascii.unhexlify(self.ToAddress.encode('utf-8')))
        data.reverse()
        return UInt160(data=data)

    @property
    def OutputAddr(self):
        return Crypto.ToAddress(self.OutputHash)

    @property
    def AssetId(self):
        return self.Output.AssetId

    @property
    def AssetName(self):
        if self.AssetId == GetBlockchain().SystemShare().Hash:
            return 'NEO'
        elif self.AssetId == GetBlockchain().SystemCoin().Hash:
            return 'Gas'
        return 'Unknown'

    @property
    def Output(self):
        tx, height = GetBlockchain().GetTransaction(self.TXHash)
        output = tx.outputs[self.Index]
        return output

    @property
    def InputHash(self):
        data = bytearray(binascii.unhexlify(self.FromAddress.encode('utf-8')))
        data.reverse()
        return UInt160(data=data)

    @property
    def InputAddr(self):
        return Crypto.ToAddress(self.InputHash)

    def ToJson(self):
        jsn = {
            'To': self.OutputAddr,
            'From': self.InputHash.ToString(),
            'Amount': self.Amount,
            'Index': self.Index,
            'TxId': self.Hash,
            'Complete': self.IsComplete
        }

        return jsn
