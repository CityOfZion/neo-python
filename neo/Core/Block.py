# -*- coding:utf-8 -*-

from neo.Network.Mixins import InventoryMixin
from neo.Network.InventoryType import InventoryType
from neo.Core.BlockBase import BlockBase
from neo.Core.TX.Transaction import Transaction,TransactionType
from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.Cryptography.MerkleTree import MerkleTree
from json import dumps
import sys
from autologging import logged
from neo.Core.Header import Header
from neo.Core.Witness import Witness
import json
from neo.Fixed8 import Fixed8

#  < summary >
#  区块或区块头
#  < / summary >

@logged
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
                 script=None, transactions=[], build_root=False):

        super(Block, self).__init__()
        self.Version = 0
        self.PrevHash = prevHash
        self.Timestamp = timestamp
        self.Index = index
        self.ConsensusData = consensusData
        self.NextConsensus = nextConsensus
        self.Script = script
        self.Transactions = transactions
        if build_root:
            self.RebuildMerkleRoot()

    """
        'PrevHash' : self.PrevHash,
        'MerkleRoot' : self.MerkleRoot,
        'Timestamp' : self.Timestamp,
        'Index' : self.Index,
        'ConsensusData' : self.ConsensusData,
        'NextConsensus' : self.NextConsensus,
        'Script' : self.Script,

    """

    def Header(self):
        if not self.__header:

            self.__header = Header(self.PrevHash, self.MerkleRoot, self.Timestamp,
                            self.Index, self.ConsensusData, self.NextConsensus, self.Script)

        return self.__header


    def Size(self):
        s = super(Block,self).Size()
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
        amount=0
        for tx in self.Transactions:
            if type(tx.SystemFee()) is int:
                raise Exception("TX %s is baddddddd %s %s" % (tx, tx.Type))
            elif type(tx.SystemFee().value) is Fixed8:
                raise Exception("TX ISSS BADD:::: %s %s" % (tx, tx.Type))
            amount += tx.SystemFee().value
        return Fixed8(amount)
#        return Fixed8(sum( tx.SystemFee().value for tx in self.Transactions))


    #  < summary >
    #  反序列化
    #  < / summary >
    #  < param name = "reader" > 数据来源 < / param >
    def Deserialize(self, reader):
        super(Block,self).Deserialize(reader)

        self.Transactions = []
        byt = reader.ReadVarInt()
        transaction_length = byt

        if transaction_length < 1:
            raise Exception('Invalid format')

        for i in range(0, transaction_length):
            try:
                tx = Transaction.DeserializeFrom(reader)
                self.Transactions.append(tx)
            except Exception as e:
                self.__log.debug("could not deserialize tx: %s " % e)
                self.__log.debug("BLOCK  %s " % self.Index)



        if MerkleTree.ComputeRoot( [tx.HashToByteString() for tx in self.Transactions]) != self.MerkleRoot:
            raise Exception("Merkle Root Mismatch")


    #  < summary >
    #  比较当前区块与指定区块是否相等
    #  < / summary >
    #  < param name = "other" > 要比较的区块 < / param >
    #  < returns > 返回对象是否相等 < / returns >

    def Equals(self, other):

        if other is None: return False
        if other is self: return True
        return self.Hash() == other.Hash()



    @staticmethod
    def FromTrimmedData(byts, index, transaction_method=None):

        block = Block()
        block.__is_trimmed = True
        ms = MemoryStream(byts)
        reader = BinaryReader(ms)

        block.DeserializeUnsigned(reader)
        reader.ReadByte()
        witness = Witness()
        witness.Deserialize(reader)
        block.witness = witness

        block.Transactions = reader.ReadHashes()
        return block

    # < summary >
    # 获得区块的HashCode
    # < / summary >
    # < returns > 返回区块的HashCode < / returns >
    def GetHashCode(self):
        return self.Hash()

    # < summary >
    # 根据区块中所有交易的Hash生成MerkleRoot
    # < / summary >
    def RebuildMerkleRoot(self):
        self.__log.debug("Rebuilding merlke root!")
        if self.Transactions is not None and len(self.Transactions) > 0:
            self.MerkleRoot = MerkleTree.ComputeRoot([tx.HashToByteString() for tx in self.Transactions])

    # < summary >
    # 序列化
    # < / summary >
    # < param name = "writer" > 存放序列化后的数据 < / param >
    def Serialize(self, writer):
        super(BlockBase,self).Serialize(writer)
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

        return json

    # < summary >
    # 把区块对象变为只包含区块头和交易Hash的字节数组，去除交易数据
    # < / summary >
    # < returns > 返回只包含区块头和交易Hash的字节数组 < / returns >
    def Trim(self):
        ms = MemoryStream()
        writer = BinaryWriter(ms)
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)
        writer.WriteHashes([tx.HashToByteString() for tx in self.Transactions])
        retVal = ms.ToArray()
        ms.Cleanup()
        ms = None
        return retVal

    # < summary >
    # 验证该区块是否合法
    # < / summary >
    # < paramname = "completely" > 是否同时验证区块中的每一笔交易 < / param >
    # < returns > 返回该区块的合法性，返回true即为合法，否则，非法。 < / returns >
    def Verify(self, completely=False):

        self.__log.debug("Verifying BLOCK!!")
        from neo.Blockchain import GetBlockchain,GetConsensusAddress

        res = super(Block, self).Verify()
        if not res: return False

        #first TX has to be a miner transaction. other tx after that cant be miner tx
        if self.Transactions[0].Type != TransactionType.MinerTransaction: return False
        for tx in self.Transactions[1:]:
            if tx.Type == TransactionType.MinerTransaction: return False


        if completely:
            bc = GetBlockchain()

            if self.NextConsensus != GetConsensusAddress(bc.GetValidators(self.Transactions).ToArray()):
                return False
            
            for tx in self.Transactions:
                if not tx.Verify():
                    pass
            self.__log.debug("Blocks cannot be fully validated at this moment.  please pass completely=False")
            raise NotImplementedError()
            ## do this below!
            #foreach(Transaction tx in Transactions)
            #if (!tx.Verify(Transactions.Where(p = > !p.Hash.Equals(tx.Hash)))) return false;
            #Transaction tx_gen = Transactions.FirstOrDefault(p= > p.Type == TransactionType.MinerTransaction);
            #if (tx_gen?.Outputs.Sum(p = > p.Value) != CalculateNetFee(Transactions)) return false;

        return True
            
            