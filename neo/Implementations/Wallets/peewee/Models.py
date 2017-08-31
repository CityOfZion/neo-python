
from peewee import *
from .PWDatabase import PWDatabase

class ModelBase(Model):
    class Meta:
        database = PWDatabase.DBProxy()

class Account(ModelBase):

    PrivateKeyEncrypted = CharField()
    PublicKeyHash = CharField()


class Address(ModelBase):
    ScriptHash = CharField(unique=True)

class Coin(ModelBase):
    TxId = CharField(unique=True)
    Index = IntegerField()
    AssetId = CharField()
    Value = IntegerField()
    ScriptHash = CharField(unique=True)
    State = IntegerField()
    Address = ForeignKeyField(Address)


class Contract(ModelBase):
    RawData = CharField()
    ScriptHash = CharField(unique=True)
    PublicKeyHash = CharField()
#    Account = ForeignKeyField(Account)
#    Address = ForeignKeyField(Address)

class Key(ModelBase):
    Name = CharField()
    Value = CharField()

class Transaction(ModelBase):
    Hash = CharField(unique=True)
    TransactionType = IntegerField()
    RawData = CharField()
    Height = IntegerField()
    DateTime = DateTimeField()

class TransactionInfo(ModelBase):
    CoreTransaction = ForeignKeyField(Transaction)
    Height = IntegerField()
    DateTime = DateTimeField()


