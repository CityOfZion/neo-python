
from peewee import *
from .PWDatabase import PWDatabase
from neo.Cryptography.Crypto import Crypto
from neocore.UInt160 import UInt160


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
