# -*- coding:utf-8 -*-

from AntShares.Network.Mixins import InventoryMixin
from AntShares.Network.InventoryType import InventoryType
from AntShares.Core.BlockBase import BlockBase
from AntShares.Core.Transaction import Transaction,TransactionType
from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryReader import BinaryReader
from AntShares.IO.BinaryWriter import BinaryWriter
from AntShares.Cryptography.MerkleTree import MerkleTree
from json import dumps
import sys

#  < summary >
#  区块或区块头
#  < / summary >
class Block(BlockBase, InventoryMixin):

    #  < summary >
    #  交易列表
    #  < / summary >
    Transactions = []

    #  < summary >
    #  该区块的区块头
    #  < / summary >

    __header = None

    #  < summary >
    #  资产清单的类型
    #  < / summary >
    InventoryType = InventoryType.Block

    def Header(self):
        if not self.__header:


            self.__header = {
                'PrevHash' : self.PrevHash,
                'MerkleRoot' : self.MerkleRoot,
                'Timestamp' : self.Timestamp,
                'Index' : self.Index,
                'ConsensusData' : self.ConsensusData,
                'NextConsensus' : self.NextConsensus,
                'Script' : self.Script,
            }

        return self.__header


    def Size(self):
        s = self.Size()
        s = s + sys.getsizeof(self.Transactions)

        return s


    def CalculatneNetFee(self, transactions):
#        Transaction[] ts = transactions.Where(p= > p.Type != TransactionType.MinerTransaction & & p.Type != TransactionType.ClaimTransaction).ToArray();
#        Fixed8 amount_in = ts.SelectMany(p= > p.References.Values.Where(o= > o.AssetId == Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
#        Fixed8 amount_out = ts.SelectMany(p= > p.Outputs.Where(o= > o.AssetId == Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
#        Fixed8 amount_sysfee = ts.Sum(p= > p.SystemFee);
#        return amount_in - amount_out - amount_sysfee;
        return 0


    #  < summary >
    #  反序列化
    #  < / summary >
    #  < param name = "reader" > 数据来源 < / param >
    def Deserialize(self, reader):
        super(BlockBase,self).Deserialize(reader)
        self.Transactions = [ Transaction(reader.ReadVarInt(0x10000)),]

        if len(self.Transactions) < 1:
            raise Exception('Invalid format')

        [tx.DeserializeFrom(reader) for tx in self.Transactions]

        if MerkleTree.ComputeRoot( [tx.Hash() for tx in self.Transactions]) != self.MerkleRoot:
            raise Exception('Invalid Format')


    #  < summary >
    #  比较当前区块与指定区块是否相等
    #  < / summary >
    #  < param name = "other" > 要比较的区块 < / param >
    #  < returns > 返回对象是否相等 < / returns >

    def Equals(self, other):

#        if (ReferenceEquals(this, other)) return true;
#        if (ReferenceEquals(null, other)) return false;

        return self.Hash() == other.Hash()


    @staticmethod
    def FromTrimmedData(bytes, index, transaction_method):
        block = Block()
#        ms = MemoryStream(bytes, index, (len(bytes) - index))
        ms = MemoryStream()
        reader = BinaryReader(ms)

        block.DeserializeUnsigned(reader)
        reader.readByte()
        block.Script = reader.readSerializableArray()
        block.Transactions = []
        for i in range(0, reader.readVarInt()):
            block.Transactions[i] = transaction_method( reader.readSerializableArray())

    # < summary >
    # 获得区块的HashCode
    # < / summary >
    # < returns > 返回区块的HashCode < / returns >
    def GetHashCode(self):
        return self.Hash().GetHashCode()

    # < summary >
    # 根据区块中所有交易的Hash生成MerkleRoot
    # < / summary >
    def RebuildMerkleRoot(self):
        self.MerkleRoot = MerkleTree.ComputeRoot([tx.Hash() for tx in self.Transactions])

    # < summary >
    # 序列化
    # < / summary >
    # < param name = "writer" > 存放序列化后的数据 < / param >
    def Serialize(self, writer):
        super(BlockBase,self).Serialize(writer)
        writer.writeSerializableArray(self.Transactions)

    # < summary >
    # 变成json对象
    # < / summary >
    # < returns > 返回json对象 < / returns >
    def ToJson(self):

        return dumps(self)

    # < summary >
    # 把区块对象变为只包含区块头和交易Hash的字节数组，去除交易数据
    # < / summary >
    # < returns > 返回只包含区块头和交易Hash的字节数组 < / returns >
    def Trim(self):
        ms = MemoryStream()
        writer = BinaryWriter(ms)

        self.SerializeUnsigned(writer)
        writer.writeByte(1)
        writer.writeSerializableArray(self.Script)
        writer.writeSerializableArray([tx.Hash() for tx in self.Transactions])

        return ms.toArray()

    # < summary >
    # 验证该区块是否合法
    # < / summary >
    # < paramname = "completely" > 是否同时验证区块中的每一笔交易 < / param >
    # < returns > 返回该区块的合法性，返回true即为合法，否则，非法。 < / returns >
    def Verify(self, completely=False):

        if not self.Verify(): return False

        for tx in self.Transactions:
            if tx.Type == TransactionType.MinerTransaction: return False
            
        if completely:
            if self.NextConsensus != Blockchain.GetConsensusAddress(Blockchain.Default.GetValidators(self.Transactions).ToArray()):
                return False
            
            for tx in self.Transactions:
                if not tx.Verify():
                    pass

            raise NotImplementedError()
            ## do this below!
            #foreach(Transaction tx in Transactions)
            #if (!tx.Verify(Transactions.Where(p = > !p.Hash.Equals(tx.Hash)))) return false;
            #Transaction tx_gen = Transactions.FirstOrDefault(p= > p.Type == TransactionType.MinerTransaction);
            #if (tx_gen?.Outputs.Sum(p = > p.Value) != CalculateNetFee(Transactions)) return false;

        return True
            
            