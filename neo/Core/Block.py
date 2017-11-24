import sys

from logzero import logger

from neo.Network.Mixins import InventoryMixin
from neo.Network.InventoryType import InventoryType
from neo.Core.BlockBase import BlockBase
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.Cryptography.MerkleTree import MerkleTree
from neo.Core.Header import Header
from neo.Core.Witness import Witness
from neo.Fixed8 import Fixed8
from neo.Blockchain import GetBlockchain
from neo.Settings import settings


class Block(BlockBase, InventoryMixin):

    #  < summary >
    #  交易列表
    #  < / summary >
    Transactions = []

    #  < summary >
    #  该区块的区块头
    #  < / summary >

    __header = None

    __is_trimmed = False
    #  < summary >
    #  资产清单的类型
    #  < / summary >
    InventoryType = InventoryType.Block

    def __init__(self, prevHash=None, timestamp=None, index=None,
                 consensusData=None, nextConsensus=None,
                 script=None, transactions=None, build_root=False):

        super(Block, self).__init__()
        self.Version = 0
        self.PrevHash = prevHash
        self.Timestamp = timestamp
        self.Index = index
        self.ConsensusData = consensusData
        self.NextConsensus = nextConsensus
        self.Script = script

        if transactions:

            self.Transactions = transactions
        else:
            self.Transactions = []

        if build_root:
            self.RebuildMerkleRoot()

    @property
    def FullTransactions(self):

        is_trimmed = False
        try:
            tx = self.Transactions[0]
            if type(tx) is str:
                is_trimmed = True
        except Exception as e:
            pass

        if not is_trimmed:
            return self.Transactions

        txs = []
        for hash in self.Transactions:
            tx, height = GetBlockchain().GetTransaction(hash)
            txs.append(tx)

        self.Transactions = txs

        return self.Transactions

    @property
    def Header(self):
        if not self.__header:

            self.__header = Header(self.PrevHash, self.MerkleRoot, self.Timestamp,
                                   self.Index, self.ConsensusData, self.NextConsensus, self.Script)

        return self.__header

    def Size(self):
        s = super(Block, self).Size()
        s = s + sys.getsizeof(self.Transactions)

        return s

    def CalculatneNetFee(self, transactions):
        #        Transaction[] ts = transactions.Where(p= > p.Type != TransactionType.MinerTransaction & & p.Type != TransactionType.ClaimTransaction).ToArray();
        #        Fixed8 amount_in = ts.SelectMany(p= > p.References.Values.Where(o= > o.AssetId == Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
        #        Fixed8 amount_out = ts.SelectMany(p= > p.Outputs.Where(o= > o.AssetId == Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
        #        Fixed8 amount_sysfee = ts.Sum(p= > p.SystemFee);
        #        return amount_in - amount_out - amount_sysfee;
        return 0

    def TotalFees(self):
        amount = Fixed8.Zero()
        for tx in self.Transactions:
            amount += tx.SystemFee()
        return amount

    #  < summary >
    #  反序列化
    #  < / summary >
    #  < param name = "reader" > 数据来源 < / param >
    def Deserialize(self, reader):
        super(Block, self).Deserialize(reader)

        self.Transactions = []
        byt = reader.ReadVarInt()
        transaction_length = byt

        if transaction_length < 1:
            raise Exception('Invalid format')

        for i in range(0, transaction_length):
            tx = Transaction.DeserializeFrom(reader)
            self.Transactions.append(tx)

        if MerkleTree.ComputeRoot([tx.Hash for tx in self.Transactions]) != self.MerkleRoot:
            raise Exception("Merkle Root Mismatch")

    #  < summary >
    #  比较当前区块与指定区块是否相等
    #  < / summary >
    #  < param name = "other" > 要比较的区块 < / param >
    #  < returns > 返回对象是否相等 < / returns >

    def Equals(self, other):

        if other is None:
            return False
        if other is self:
            return True
        return self.Hash == other.Hash

    @staticmethod
    def FromTrimmedData(byts, index=None, transaction_method=None):

        block = Block()
        block.__is_trimmed = True
        ms = StreamManager.GetStream(byts)
        reader = BinaryReader(ms)

        block.DeserializeUnsigned(reader)
        reader.ReadByte()
        witness = Witness()
        witness.Deserialize(reader)
        block.witness = witness

        block.Transactions = reader.ReadHashes()

        StreamManager.ReleaseStream(ms)

        return block

    # < summary >
    # 获得区块的HashCode
    # < / summary >
    # < returns > 返回区块的HashCode < / returns >
    def GetHashCode(self):
        return self.Hash

    # < summary >
    # 根据区块中所有交易的Hash生成MerkleRoot
    # < / summary >
    def RebuildMerkleRoot(self):
        logger.debug("Rebuilding merlke root!")
        if self.Transactions is not None and len(self.Transactions) > 0:
            self.MerkleRoot = MerkleTree.ComputeRoot([tx.Hash for tx in self.Transactions])

    # < summary >
    # 序列化
    # < / summary >
    # < param name = "writer" > 存放序列化后的数据 < / param >
    def Serialize(self, writer):
        super(BlockBase, self).Serialize(writer)
        writer.WriteSerializableArray(self.Transactions)

    # < summary >
    # 变成json对象
    # < / summary >
    # < returns > 返回json对象 < / returns >
    def ToJson(self):
        json = super(Block, self).ToJson()
        if self.__is_trimmed:
            json['tx'] = self.Transactions
        else:
            json['tx'] = [tx.ToJson() for tx in self.Transactions]

        json['sys_fee'] = GetBlockchain().GetSysFeeAmount(self.Hash)
        return json

    # < summary >
    # 把区块对象变为只包含区块头和交易Hash的字节数组，去除交易数据
    # < / summary >
    # < returns > 返回只包含区块头和交易Hash的字节数组 < / returns >
    def Trim(self):
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)

        writer.WriteHashes([tx.Hash.ToBytes() for tx in self.Transactions])
        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        return retVal

    # < summary >
    # 验证该区块是否合法
    # < / summary >
    # < paramname = "completely" > 是否同时验证区块中的每一笔交易 < / param >
    # < returns > 返回该区块的合法性，返回true即为合法，否则，非法。 < / returns >
    def Verify(self, completely=False):

        res = super(Block, self).Verify()
        if not res:
            return False

        logger.debug("Verifying BLOCK!!")
        from neo.Blockchain import GetBlockchain, GetConsensusAddress

        # first TX has to be a miner transaction. other tx after that cant be miner tx
        if self.Transactions[0].Type != TransactionType.MinerTransaction:
            return False
        for tx in self.Transactions[1:]:
            if tx.Type == TransactionType.MinerTransaction:
                return False

        if completely:
            bc = GetBlockchain()

            if self.NextConsensus != GetConsensusAddress(bc.GetValidators(self.Transactions).ToArray()):
                return False

            for tx in self.Transactions:
                if not tx.Verify():
                    pass
            logger.error("Blocks cannot be fully validated at this moment.  please pass completely=False")
            raise NotImplementedError()
            # do this below!
            # foreach(Transaction tx in Transactions)
            # if (!tx.Verify(Transactions.Where(p = > !p.Hash.Equals(tx.Hash)))) return false;
            # Transaction tx_gen = Transactions.FirstOrDefault(p= > p.Type == TransactionType.MinerTransaction);
            # if (tx_gen?.Outputs.Sum(p = > p.Value) != CalculateNetFee(Transactions)) return false;

        return True
