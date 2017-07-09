# -*- coding: UTF-8 -*-
from AntShares.Cryptography import *
from AntShares.IO import *
from AntShares.Wallets import *
from .Mixins import VerifiableMixin
from AntShares.Cryptography.Crypto import *
from AntShares.Core.Blockchain import Blockchain
from AntShares.Core.Helper import Helper
import json
import ctypes
import hashlib

class BlockBase(VerifiableMixin):

    #  <summary>
    #  区块版本
    #  </summary>
    Version=None
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
        if reader.ReadByte() != 1:
            raise Exception('Incorrect format')
        self.Script = reader.readSerializableArray(self.scripts)


    def DeserializeUnsigned(self, reader):
        self.Version = reader.readUInt32()
        self.PrevHash = reader.readSerializableArray()
        self.MerkleRoot = reader.readSerializableArray()
        self.Timestamp = reader.readUInt32()
        self.Index = reader.readUInt32()
        self.ConsensusData = reader.readUInt64()
        self.NextConsensus = reader.readSerializableArray()

    def SerializeUnsigned(self, writer):
        writer.writeUInt32(self.Version)
        writer.writeSerializableArray(self.PrevHash)
        writer.writeSerializableArray(self.MerkleRoot)
        writer.writeUInt32(self.Timestamp)
        writer.writeUInt32(self.Index)
        writer.writeUInt64(self.ConsensusData)
        writer.writeSerializableArray(self.NextConsensus)

    def GetHashData(self):
        raise NotImplementedError('Not Implemented')

    def GetMessage(self):
        return self.GetHashData()


    def GetScriptHashesForVerifying(self):
        if self.PrevHash == None:
            return [ self.Script.VerificationScript.ToScriptHash()]

        prev_header = Blockchain.Default().GetHeader(self.PrevHash)
        if prev_header == None:
            raise Exception('Invalid operation')
        return [ prev_header.NextConsensus ]



    def Serialize(self, writer):
        self.SerializeUnsigned(writer)
        writer.writeByte(1)
        writer.writeSerializableArray(self.Script)



    def ToArray(self):
        raise NotImplementedError()

    def ToJson(self):
        json = {}
        json["hash"] = self.__hash.toString()

        json["size"] = self.Size
        json["version"] = self.Version
        json["previousblockhash"] = self.PrevHash.ToString()
        json["merkleroot"] = self.MerkleRoot.ToString()
        json["time"] = self.Timestamp
        json["index"] = self.Index
        json["nonce"] = self.ConsensusData.ToString("x16")
        json["nextconsensus"] = self.Wallet.ToAddress(self.NextConsensus)
        json["script"] = self.Script.ToJson()
        return json

    def Verify(self):
        if self.Hash == Blockchain.GenesisBlock.Hash: return True

        if Blockchain.Default().ContainsBlock(self.Hash): return True

        prev_header = Blockchain.Default().GetHeader(self.PrevHash)

        if prev_header == None: return False

        if prev_header.Index + 1 != self.Index: return False

        if prev_header.Timestamp >= self.Timestamp: return False

        if not Helper.VerifyScripts(self): return False

        return True

