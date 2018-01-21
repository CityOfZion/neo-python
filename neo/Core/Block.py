import sys
from logzero import logger
from neo.Network.Mixins import InventoryMixin
from neo.Network.InventoryType import InventoryType
from neo.Core.BlockBase import BlockBase
from neo.Core.TX.Transaction import Transaction, TransactionType
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager
from neocore.Cryptography.MerkleTree import MerkleTree
from neo.Core.Header import Header
from neo.Core.Witness import Witness
from neocore.Fixed8 import Fixed8
from neo.Blockchain import GetBlockchain


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
        """
        Create an instance.

        Args:
            prevHash (UInt160):
            timestamp (int): seconds since Unix epoch.
            index (int): block height.
            consensusData (int): uint64.
            nextConsensus (UInt160):
            script (neo.Core.Witness): script used to verify the block.
            transactions (list): of neo.Core.TX.Transaction.Transaction objects.
            build_root (bool): flag indicating whether to rebuild the merkle root.
        """

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
        """
        Get the list of full Transaction objects.

        Note: Transactions can be trimmed to contain only the header and the hash. This will get the full data if
        trimmed transactions are found.

        Returns:
            list: of neo.Core.TX.Transaction.Transaction objects.
        """
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
        """
        Get the block header.

        Returns:
            neo.Core.Header:
        """
        if not self.__header:
            self.__header = Header(self.PrevHash, self.MerkleRoot, self.Timestamp,
                                   self.Index, self.ConsensusData, self.NextConsensus, self.Script)

        return self.__header

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
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
        """
        Get the total transaction fees in the block.

        Returns:
            Fixed8:
        """
        amount = Fixed8.Zero()
        for tx in self.Transactions:
            amount += tx.SystemFee()
        return amount

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
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

    def Equals(self, other):
        """
        Test for equality.

        Args:
            other (obj):

        Returns:
            bool: True `other` equals self.
        """
        if other is None:
            return False
        if other is self:
            return True
        return self.Hash == other.Hash

    @staticmethod
    def FromTrimmedData(byts, index=None, transaction_method=None):
        """
        Deserialize a block from raw bytes.

        Args:
            byts:
            index: UNUSED
            transaction_method: UNUSED

        Returns:
            Block:
        """
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

    def GetHashCode(self):
        """
        Get the hash code of the block.

        Returns:
            UInt256:
        """
        return self.Hash

    def RebuildMerkleRoot(self):
        """Rebuild the merkle root of the block"""
        logger.debug("Rebuilding merkle root!")
        if self.Transactions is not None and len(self.Transactions) > 0:
            self.MerkleRoot = MerkleTree.ComputeRoot([tx.Hash for tx in self.Transactions])

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(BlockBase, self).Serialize(writer)
        writer.WriteSerializableArray(self.Transactions)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        json = super(Block, self).ToJson()
        if self.__is_trimmed:
            json['tx'] = self.Transactions
        else:
            json['tx'] = [tx.ToJson() for tx in self.Transactions]

        json['sys_fee'] = GetBlockchain().GetSysFeeAmount(self.Hash)
        return json

    def Trim(self):
        """
        Returns a byte array that contains only the block header and transaction hash.

        Returns:
            bytes:
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)

        writer.WriteHashes([tx.Hash.ToBytes() for tx in self.Transactions])
        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        return retVal

    def Verify(self, completely=False):
        """
        Verify the integrity of the block.

        Args:
            completely: (Not functional at this time).

        Returns:
            bool: True if valid. False otherwise.
        """
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
