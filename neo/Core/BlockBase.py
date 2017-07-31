# -*- coding: UTF-8 -*-
from .Mixins import VerifiableMixin
from neo.Cryptography.Crypto import *
from neo.Core.Helper import Helper
import ctypes
from neo.Blockchain import GetBlockchain,GetGenesis
from neo.Core.Witness import Witness
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream
import pprint

class BlockBase(VerifiableMixin):

    #  <summary>
    #  区块版本
    #  </summary>
    Version=0
    #  <summary>
    #  前一个区块的散列值
    #  </summary>
    PrevHash=None
    #  <summary>
    #  该区块中所有交易的Merkle树的根
    #  </summary>
    MerkleRoot = None
    #  <summary>
    #  时间戳
    #  </summary>
    Timestamp = None
    #  <summary>
    #  区块高度
    #  </summary>
    Index =0

    ConsensusData=None
    #  <summary>
    #  下一个区块的记账合约的散列值
    #  </summary>
    NextConsensus = None
    #  <summary>
    #  用于验证该区块的脚本
    #  </summary>
    Script = None

    __hash = None



    def Hash(self):
        if not self.__hash:
            self.__hash = Crypto.Hash256(self.GetHashData())

        return self.__hash


    def Size(self):
#            sizeof(uint) + PrevHash.Size + MerkleRoot.Size + sizeof(uint) + sizeof(uint) + sizeof(
#                ulong) + NextConsensus.Size + 1 + Script.Size;

        uintsize = ctypes.sizeof(ctypes.c_uint)
        ulongsize = ctypes.sizeof(ctypes.c_ulong)
        return uintsize + self.PrevHash.Size() + self.MerkleRoot.Size() + uintsize + uintsize + ulongsize + self.NextConsensus.Size() + 1 + self.Script.Size()


    def Deserialize(self, reader):
        self.DeserializeUnsigned(reader)
        byt = reader.ReadByte()
        print("Byte to read:: %s %s" % (type(byt),byt))
        if int(byt) != 1:
            raise Exception('Incorrect format')

        print("deseriailizing witness")
        witness = Witness()
        witness.Deserialize(reader)
        self.Script = witness
        print("deserialized witness")


    def DeserializeUnsigned(self, reader):
        print("DEserializing unsigned block")
        self.Version = reader.ReadUInt32()
        print("DEserializing unsigned 1")
        self.PrevHash = binascii.hexlify( reader.ReadUInt256())
        print("DEserializing unsigned 2")
        self.MerkleRoot = binascii.hexlify( reader.ReadUInt256())
        print("DEserializing unsigned 3")
        self.Timestamp = reader.ReadUInt32()
        self.Index = reader.ReadUInt32()
        print("DEserializing unsigned 4")
        self.ConsensusData =  reader.ReadUInt64()
        print("DEserializing unsigned 5")
        self.NextConsensus = reader.ReadUInt160()
        print("NEXT CONSENSUS: %s " % self.NextConsensus)
        print("DEserializing unsigned 6")
        print(self.ToJson())

    def SerializeUnsigned(self, writer):
        writer.WriteUInt32(self.Version)
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt256(self.MerkleRoot)
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt32(self.Index)
        writer.WriteUInt64(self.ConsensusData)
        writer.WriteUInt160(self.NextConsensus)

    def GetHashData(self):

        ms = MemoryStream()
        writer = BinaryWriter(ms)

        self.SerializeUnsigned(writer)
        return ms.ToArray()


    def GetMessage(self):
        return self.GetHashData()


    def GetScriptHashesForVerifying(self):
        if self.PrevHash == None:
            return [ self.Script.VerificationScript.ToScriptHash()]

        prev_header = GetBlockchain().GetHeader(self.PrevHash)
        if prev_header == None:
            raise Exception('Invalid operation')
        return [ prev_header.NextConsensus ]



    def Serialize(self, writer):
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)
#        writer.WriteSerializableArray(self.Script)



    def ToArray(self):
        raise NotImplementedError()

    def ToJson(self):
        json = {}
        json["hash"] = self.Hash()

        json["size"] = self.Size
        json["version"] = self.Version
        json["previousblockhash"] = self.PrevHash
        json["merkleroot"] = self.MerkleRoot
        json["time"] = self.Timestamp
        json["index"] = self.Index
        json['next_consensus'] = self.NextConsensus
        json["consensus data"] = self.ConsensusData
#        json["nextconsensus"] = self.Wallet.ToAddress(self.NextConsensus)
        json["script"] = self.Script
        return json

    def Verify(self):
        if self.Hash == GetGenesis().Hash: return True

        if GetBlockchain().ContainsBlock(self.Hash): return True

        prev_header = GetBlockchain().GetHeader(self.PrevHash)

        if prev_header == None: return False

        if prev_header.Index + 1 != self.Index: return False

        if prev_header.Timestamp >= self.Timestamp: return False

        if not Helper.VerifyScripts(self): return False

        return True

