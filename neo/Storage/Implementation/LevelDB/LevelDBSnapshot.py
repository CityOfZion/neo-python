import neo.Storage.Common.Snapshot
import neo.Storage.Common.CloneSnapshot
from neo.Storage.Implementation.LevelDB.LevelDBCache import LevelDBCache
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Core.State.BlockState import BlockState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.SpentCoinState import SpentCoinState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.TransactionState import TransactionState
from neo.Core.TX.Transaction import Transaction
import binascii
from neo.Core.UInt256 import UInt256


class LevelDBSnapshot(neo.Storage.Common.Snapshot.Snapshot):

    def __init__(self, _db):
        super(LevelDBSnapshot, self).__init__()
        self.db = _db  # type: LevelDBImpl
        self.snapshot = self.db._db.snapshot()
        self.batch = self.db._db.write_batch()
        self.Blocks = LevelDBCache(self.db, self.batch, DBPrefix.DATA_Block, BlockState)
        self.Transactions = LevelDBCache(self.db, self.batch, DBPrefix.DATA_Transaction, TransactionState)
        self.Accounts = LevelDBCache(self.db, self.batch, DBPrefix.ST_Account, AccountState)
        self.UnspentCoins = LevelDBCache(self.db, self.batch, DBPrefix.ST_Coin, UnspentCoinState)
        self.SpentCoins = LevelDBCache(self.db, self.batch, DBPrefix.ST_SpentCoin, SpentCoinState)
        self.Assets = LevelDBCache(self.db, self.batch, DBPrefix.ST_Asset, AssetState)
        self.Validators = LevelDBCache(self.db, self.batch, DBPrefix.ST_Validator, ValidatorState)
        self.Contracts = LevelDBCache(self.db, self.batch, DBPrefix.ST_Contract, ContractState)
        self.Storages = LevelDBCache(self.db, self.batch, DBPrefix.ST_Storage, StorageItem)

    def Commit(self):
        super(LevelDBSnapshot, self).Commit()
        self.batch.write()

    def Dispose(self):
        self.snapshot.close()

    def Clone(self):
        return neo.Storage.Common.CloneSnapshot.CloneSnapshot(self)

    def GetTransaction(self, hash):
        if type(hash) is str:
            hash = hash.encode('utf-8')
        elif type(hash) is UInt256:
            hash = hash.ToBytes()

        # TODO: should first look in cache
        # tx = self.Transactions.TryGet(hash)
        # if tx is not None:
        #     return tx

        out = self.db.get(DBPrefix.DATA_Transaction + hash)
        if out is not None:
            out = bytearray(out)
            height = int.from_bytes(out[:4], 'little')
            out = out[4:]
            outhex = binascii.unhexlify(out)
            return Transaction.DeserializeFromBufer(outhex, 0), height
        return None, -1
