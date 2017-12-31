
from peewee import *
from .PWDatabase import PWDatabase
from neo.Cryptography.Crypto import Crypto
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256
import pdb
import binascii

class ModelBase(Model):
    class Meta:
        database = PWDatabase.DBProxy()


class Account(ModelBase):
    Id = PrimaryKeyField()
    PrivateKeyEncrypted = CharField(unique=True)
    PublicKeyHash = CharField()


class Address(ModelBase):
    Id = PrimaryKeyField()
    ScriptHash = CharField(unique=True)
    IsWatchOnly = BooleanField(default=False)

    def ToString(self):
        return Crypto.ToAddress(UInt160(data=self.ScriptHash))


class NamedAddress(ModelBase):
    Id = PrimaryKeyField()
    ScriptHash = CharField(unique=True)
    Title = CharField()

    def UInt160ScriptHash(self):
        return UInt160(data=self.ScriptHash)

    def ToString(self):
        return Crypto.ToAddress(UInt160(data=self.ScriptHash))


class Coin(ModelBase):
    Id = PrimaryKeyField()
    TxId = CharField()
    Index = IntegerField()
    AssetId = CharField()
    Value = IntegerField()
    ScriptHash = CharField()
    State = IntegerField()
    Address = ForeignKeyField(Address)


class Contract(ModelBase):
    Id = PrimaryKeyField()
    RawData = CharField()
    ScriptHash = CharField()
    PublicKeyHash = CharField()
    Account = ForeignKeyField(Account, null=True)
    Address = ForeignKeyField(Address)


class Key(ModelBase):
    Id = PrimaryKeyField()
    Name = CharField(unique=True)
    Value = CharField()


class NEP5Token(ModelBase):
    ContractHash = CharField(unique=True)
    Name = CharField()
    Symbol = CharField()
    Decimals = IntegerField()


class Transaction(ModelBase):
    Id = PrimaryKeyField()
    Hash = CharField(unique=True)
    TransactionType = IntegerField()
    RawData = CharField()
    Height = IntegerField()
    DateTime = DateTimeField()


class TransactionInfo(ModelBase):
    Id = PrimaryKeyField()
    CoreTransaction = ForeignKeyField(Transaction)
    Height = IntegerField()
    DateTime = DateTimeField()

class VINHold(ModelBase):
    Id = PrimaryKeyField()
    Index = IntegerField()
    Hash = CharField()
    FromAddress = CharField()
    ToAddress = CharField()
    Amount = IntegerField()


    @property
    def TXHash(self):
        data = bytearray(binascii.unhexlify(self.Hash.encode('utf-8')))
        data.reverse()
        return UInt256(data=data)

    @property
    def Vin(self):
        index = bytearray(self.Index.to_bytes(2,'little'))
        return index + self.TXHash.Data

    @property
    def OutputHash(self):
        data = bytearray(binascii.unhexlify(self.ToAddress.encode('utf-8')))
        data.reverse()
        return UInt160(data=data)

    @property
    def OutputAddr(self):
        return Crypto.ToAddress(self.OutputHash)

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
            'To':self.OutputAddr,
            'From':self.InputHash.ToString(),
            'Amount':self.Amount,
            'Index':self.Index,
            'TxId':self.Hash
        }

#        pdb.set_trace()
        return jsn