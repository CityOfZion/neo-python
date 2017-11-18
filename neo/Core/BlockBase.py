import ctypes
import pprint

from logzero import logger

from .Mixins import VerifiableMixin
from neo.Cryptography.Crypto import *
from neo.Cryptography.Helper import *
from neo.Core.Helper import Helper
from neo.Blockchain import GetBlockchain, GetGenesis
from neo.Core.Witness import Witness
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256


class BlockBase(VerifiableMixin):

    #  <summary>
    #  区块版本
    #  </summary>
    Version = 0
    #  <summary>
    #  前一个区块的散列值
    #  </summary>
    PrevHash = 0  # UInt256
    #  <summary>
    #  该区块中所有交易的Merkle树的根
    #  </summary>
    MerkleRoot = 0  # UInt256
    #  <summary>
    #  时间戳
    #  </summary>
    Timestamp = None
    #  <summary>
    #  区块高度
    #  </summary>
    Index = 0

    ConsensusData = None
    #  <summary>
    #  下一个区块的记账合约的散列值
    #  </summary>
    NextConsensus = None  # UInt160
    #  <summary>
    #  用于验证该区块的脚本
    #  </summary>
    Script = None

    __hash = None

    __htbs = None

    @property
    def Hash(self):
        if not self.__hash:
            hashdata = self.RawData()
            ba = bytearray(binascii.unhexlify(hashdata))
            hash = bin_dbl_sha256(ba)
            self.__hash = UInt256(data=hash)

        return self.__hash

    def ToArray(self):
        return Helper.ToArray(self)

    def RawData(self):
        return Helper.GetHashData(self)

    @property
    def Scripts(self):
        return [self.Script]

    def Size(self):

        uintsize = ctypes.sizeof(ctypes.c_uint)
        ulongsize = ctypes.sizeof(ctypes.c_ulong)
        scriptsize = 0
        if self.Script is not None:
            scriptsize = self.Script.Size()
        return uintsize + 32 + 32 + uintsize + uintsize + ulongsize + 160 + 1 + scriptsize

    def IndexBytes(self):
        return self.Index.to_bytes(4, 'little')

    def Deserialize(self, reader):
        self.DeserializeUnsigned(reader)
        byt = reader.ReadByte()
        if int(byt) != 1:
            raise Exception('Incorrect format')

        witness = Witness()
        witness.Deserialize(reader)
        self.Script = witness

    def DeserializeUnsigned(self, reader):
        self.Version = reader.ReadUInt32()
        self.PrevHash = reader.ReadUInt256()
        self.MerkleRoot = reader.ReadUInt256()
        self.Timestamp = reader.ReadUInt32()
        self.Index = reader.ReadUInt32()
        self.ConsensusData = reader.ReadUInt64()
        self.NextConsensus = reader.ReadUInt160()

    def SerializeUnsigned(self, writer):
        writer.WriteUInt32(self.Version)
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt256(self.MerkleRoot)
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt32(self.Index)
        writer.WriteUInt64(self.ConsensusData)
        writer.WriteUInt160(self.NextConsensus)

    def GetMessage(self):
        return Helper.GetHashData(self)

    def GetScriptHashesForVerifying(self):
        # if this is the genesis block, we dont have a prev hash!
        if self.PrevHash.Data == bytearray(32):
            #            logger.info("verificiation script %s"  %(self.Script.ToJson()))
            if type(self.Script.VerificationScript) is bytes:
                return [bytearray(self.Script.VerificationScript)]
            elif type(self.Script.VerificationScript) is bytearray:
                return [self.Script.VerificationScript]
            else:
                raise Exception('Invalid Verification script')

        prev_header = GetBlockchain().GetHeader(self.PrevHash.ToBytes())
        if prev_header is None:
            raise Exception('Invalid operation')
        return [prev_header.NextConsensus]

    def Serialize(self, writer):
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)

    def ToJson(self):
        json = {}
        json["hash"] = self.Hash.ToString()

#        json["size"] = self.Size()
        json["version"] = self.Version
        json["previousblockhash"] = self.PrevHash.ToString()
        json["merkleroot"] = self.MerkleRoot.ToString()
        json["time"] = self.Timestamp
        json["index"] = self.Index
        json['next_consensus'] = self.NextConsensus.ToString()
        json["consensus data"] = self.ConsensusData
        json["script"] = '' if not self.Script else self.Script.ToJson()
        return json

    def Verify(self):
        if not self.Hash.ToBytes() == GetGenesis().Hash.ToBytes():
            return False

        bc = GetBlockchain()

        if not bc.ContainsBlock(self.Index):
            return False

        if self.Index > 0:
            prev_header = GetBlockchain().GetHeader(self.PrevHash.ToBytes())

            if prev_header is None:
                return False

            if prev_header.Index + 1 != self.Index:
                return False

            if prev_header.Timestamp >= self.Timestamp:
                return False

        # this should be done to actually verify the block
        if not Helper.VerifyScripts(self):
            return False

        return True
