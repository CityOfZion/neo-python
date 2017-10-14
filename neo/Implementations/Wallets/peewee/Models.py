
from peewee import *
from .PWDatabase import PWDatabase

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
    Name = CharField(unique=True, )
    Value = CharField()

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


