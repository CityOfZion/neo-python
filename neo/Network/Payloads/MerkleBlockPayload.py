
from neo.Core.BlockBase import BlockBase
from neo.Cryptography.MerkleTree import MerkleTree
import sys


class MerkleBlockPayload(BlockBase):

    TxCount = 0
    Hashes = []
    Flags = None

    def __init__(self, block, flags):

        if block and flags:
            tree = MerkleTree([hash for hash in block.Transactions])
            tree.Trim(flags)
            #buffer = bytearray( int(len(flags) + 7 / 8))

            self.Version = block.Version
            self.PrevHash = block.PrevHash
            self.MerkleRoot = block.MerkleRoot
            self.Timestamp = block.Timestamp
            self.Index = block.Index
            self.ConsensusData = block.ConsensusData
            self.NextConsensus = block.NextConsensus
            self.Script = block.Script
            self.TxCount = len(block.Transactions)
            self.Hashes = tree.ToHashArray()
            self.Flags = flags

    def Deserialize(self, reader):
        super(MerkleBlockPayload, self).Deserialize(reader)
        self.TxCount = reader.ReadVarInt(sys.maxsize)
        self.Hashes = reader.ReadSerializableArray()
        self.Flags = reader.ReadVarBytes()

    def Serialize(self, writer):
        super(MerkleBlockPayload, self).Serialize(writer)

        writer.WriteVarInt(self.TxCount)
        writer.Write(self.Hashes)
        writer.WriteVarBytes(self.Flags)
