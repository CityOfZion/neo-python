# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from neo.Core.Transaction import Transaction
"""

from neo.Blockchain import *
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.TransactionAttribute import *
from neo.Core.Helper import Helper
from neo.Fixed8 import Fixed8
from neo.Network.Inventory import Inventory
from neo.Network.InventoryType import InventoryType
from neo.Network.Mixins import InventoryMixin
from neo.Cryptography.Crypto import *
from neo.IO.Mixins import SerializableMixin
from neo.Helper import big_or_little

from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryReader import BinaryReader
from neo.Core.Helper import Helper
from neo import Settings

import sys
import json
from neo.Core.Witness import Witness
from autologging import logged

class TransactionResult():
    AssetId=None
    Amount=Fixed8(0)

    def __init__(self, asset_id, amount):
        self.AssetId = asset_id
        self.Amount = amount

class TransactionType(object):
    MinerTransaction = b'\x00'
    IssueTransaction = b'\x01'
    ClaimTransaction = b'\x02'
    EnrollmentTransaction = b'\x20'
    VotingTransaction = b'\x24'
    RegisterTransaction = b'\x40'
    ContractTransaction = b'\x80'
    AgencyTransaction = b'\xb0'
    PublishTransaction = b'\xd0'
    InvocationTransaction = b'\xd1'

@logged
class TransactionOutput(SerializableMixin):


    Value = None # should be fixed 8
    _ScriptHash = None
    AssetId = None

    """docstring for TransactionOutput"""
    def __init__(self, AssetId=None, Value=None, ScriptHash=None):
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Value
        self._ScriptHash = ScriptHash

    def ScriptHashRaw(self):
        return self._ScriptHash

    def ScriptHash(self):
        return hash_to_wallet_address(self._ScriptHash)

    def ScriptHashBytes(self):
        return self.ScriptHash().encode('utf-8')

    def Serialize(self, writer):
        writer.WriteUInt256(self.AssetId)
        writer.WriteFixed8(self.Value)
        writer.WriteUInt160(self._ScriptHash)

    def Deserialize(self, reader):
        self.AssetId = binascii.hexlify( reader.ReadUInt256())
        self.Value = reader.ReadFixed8()
        self._ScriptHash = reader.ReadUInt160()

    def ToJson(self):
        return {
            'AssetId': self.AssetId.decode('utf-8'),
            'Value': self.Value.value / Fixed8.D,
            'ScriptHash': self.ScriptHash()
        }

@logged
class TransactionInput(SerializableMixin):
    """docstring for TransactionInput"""

    PrevHash=None
    PrevIndex=None

    def __init__(self, prevHash=None, prevIndex=None):
        super(TransactionInput, self).__init__()
        self.PrevHash = prevHash
        self.PrevIndex = prevIndex

    def Serialize(self, writer):
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Deserialize(self, reader):
        self.PrevHash = binascii.hexlify( reader.ReadUInt256())
        self.PrevIndex = reader.ReadUInt16()

    def ToString(self):
        # to string
        return self.PrevHash + ":" + self.PrevIndex

    def ToJson(self):
        return {
            'PrevHash': self.PrevHash.encode('utf-8'),
            'PrevIndex': self.PrevIndex
        }

@logged
class Transaction(Inventory, InventoryMixin):


    Type = None

    Version = 0

    Attributes = []

    inputs = []

    outputs = []

    scripts = []

    __system_fee =  Fixed8(0)
    __network_fee = Fixed8(0)

    InventoryType = InventoryType.TX


    __hash = None
    __htbs = None

    __height = 0

    __references = {}


    """docstring for Transaction"""
    def __init__(self, inputs=[], outputs=[], attributes = [], scripts=[] ):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.Attributes= attributes
        self.scripts = scripts
        self.InventoryType = 0x01  # InventoryType TX 0x01

    def Hash(self):
        if not self.__hash:
            ba = bytearray(binascii.unhexlify(self.GetHashData()))
            hash = Crypto.Hash256(ba)
            hashhex = binascii.hexlify(hash)
            self.__hash = hashhex
        return self.__hash


    def HashToString(self):
        uint256bytes = bytearray(binascii.unhexlify(self.Hash()))
        uint256bytes.reverse()
        out = uint256bytes.hex()

        return out

    def HashToByteString(self):
        if not self.__htbs:
            self.__htbs = bytes(self.HashToString(), encoding='utf-8')
        return self.__htbs


    def GetHashData(self):
        return Helper.GetHashData(self)



    def getAllInputs(self):
        return self.inputs


    def References(self):
        if self.__references is None:

            refs = set()


            for input in self.inputs:
                tx = GetBlockchain().GetTransaction(input.PrevHash())

                if tx is not None:
                    #this aint right yet
                    refs.add({'input':input, 'output':tx.outputs[input.PrevIndex]})

            self.__references = refs
        return self.__references



    def Size(self):
        return sys.getsizeof(self.Type) + sys.getsizeof(0) \
               + sys.getsizeof(self.Attributes) + sys.getsizeof(self.inputs) + \
                    sys.getsizeof(self.outputs) + sys.getsizeof(self.scripts)


    def Height(self):
        return self.__height

    def SystemFee(self):
        return self.__system_fee

    def NetworkFee(self):
        return self.__network_fee
#        if self.__network_fee == Fixed8.Satoshi():
#            Fixed8 input = References.Values.Where(p= > p.AssetId.Equals(.SystemCoin.Hash)).Sum(p= > p.Value);
#            Fixed8 output = Outputs.Where(p= > p.AssetId.Equals(Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
#            _network_fee = input - output - SystemFee;
#            pass

#        return self.__network_fee


    def Deserialize(self, reader):

        self.DeserializeUnsigned(reader)

        self.scripts = reader.ReadSerializableArray()
        self.OnDeserialized()


    def DeserializeExclusiveData(self, reader):
        pass


    @staticmethod
    def DeserializeFromBufer(buffer, offset=0):
        mstream = MemoryStream(buffer)
        reader = BinaryReader(mstream)
        tx = Transaction.DeserializeFrom(reader)

        mstream.Cleanup()
        mstream = None
        return tx

    @staticmethod
    def DeserializeFrom(reader):
        ttype = reader.ReadByte()
        tx = None

        from neo.Core.TX.RegisterTransaction import RegisterTransaction
        from neo.Core.TX.IssueTransaction import IssueTransaction
        from neo.Core.TX.ClaimTransaction import ClaimTransaction
        from neo.Core.TX.MinerTransaction import MinerTransaction
        from neo.Core.TX.PublishTransaction import PublishTransaction
        from neo.Core.TX.InvocationTransaction import InvocationTransaction
        from neo.Core.TX.EnrollmentTransaction import EnrollmentTransaction

        if ttype == int.from_bytes( TransactionType.RegisterTransaction, 'little'):
            tx = RegisterTransaction()
        elif ttype == int.from_bytes( TransactionType.MinerTransaction, 'little'):
            tx = MinerTransaction()
        elif ttype == int.from_bytes( TransactionType.IssueTransaction, 'little'):
            tx = IssueTransaction()
        elif ttype == int.from_bytes( TransactionType.ClaimTransaction, 'little'):
            tx = ClaimTransaction()
        elif ttype == int.from_bytes( TransactionType.PublishTransaction, 'little'):
            tx = PublishTransaction()
        elif ttype == int.from_bytes(TransactionType.InvocationTransaction, 'little'):
            tx = InvocationTransaction()
        elif ttype == int.from_bytes(TransactionType.EnrollmentTransaction, 'little'):
            tx = EnrollmentTransaction()
        else:
            tx = Transaction()
            tx.Type = ttype

        tx.DeserializeUnsignedWithoutType(reader)

        tx.scripts = []
        byt = reader.ReadVarInt()
        if byt > 0:
            for i in range(0, byt):
                witness = Witness()
                witness.Deserialize(reader)
                tx.scripts = [witness]


        tx.OnDeserialized()

        return tx

    def DeserializeUnsigned(self, reader):
        if reader.ReadByte() != self.Type:
            raise Exception('incorrect type')
        self.DeserializeUnsignedWithoutType(reader)

    def DeserializeUnsignedWithoutType(self,reader):
        self.Version = reader.ReadByte()
        self.DeserializeExclusiveData(reader)
        self.Attributes = reader.ReadSerializableArray('neo.Core.TX.TransactionAttribute.TransactionAttribute')
        self.inputs = reader.ReadSerializableArray( 'neo.Core.CoinReference.CoinReference')
        self.outputs = reader.ReadSerializableArray('neo.Core.TX.Transaction.TransactionOutput')


    def Equals(self, other):
        if other is None or other is not self:
            return False
        return self.Hash() == other.Hash()

    def ToArray(self):
        return Helper.ToArray(self)

    def GetScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""

        return []
#        if not self.__references:
#            raise Exception('No References to be verified')
#
#        hashes = [ref.ScriptHash() for ref in self.References()]

#        if (References == null) throw new InvalidOperationException();
#        HashSet < UInt160 > hashes = new HashSet < UInt160 > (Inputs.Select(p= > References[p].ScriptHash));
#        hashes.UnionWith(Attributes.Where(p= > p.Usage == TransactionAttributeUsage.Script).Select(p= > newUInt160(p.Data)));
#        foreach(var group in Outputs.GroupBy(p= > p.AssetId))
#        {
#            AssetState asset = Blockchain.Default.GetAssetState(group.Key);
#            if (asset == null) throw new InvalidOperationException();
#            if (asset.AssetType.HasFlag(AssetType.DutyFlag))
#            {
#                hashes.UnionWith(group.Select(p = > p.ScriptHash));
#            }
#        }
#        return hashes.OrderBy(p= > p).ToArray();
#
#        result = self.References()
#
#        if result == None:
#            raise Exception, 'getReference None.'
#
#        for _input in self.inputs:
#            _hash = result.get(_input.toString()).scriptHash
#            hashes.update({_hash.toString(), _hash})

        # TODO
        # Blockchain.getTransaction
#        txs = [Blockchain.getTransaction(output.AssetId) for output in self.outputs]
#        for output in self.outputs:
#            tx = txs[self.outputs.index(output)]
#            if tx == None:
#                raise Exception, "Tx == None"
#            else:
#                if tx.AssetType & AssetType.DutyFlag:
#                    hashes.update(output.ScriptHash.toString(), output.ScriptHash)
#
#                    array = sorted(hashes.keys())
#                    return array


    def GetTransactionResults(self):
        if self.References() is None: return None
        raise NotImplementedError()
#        return References.Values.Select(p= > new
#        {
#            AssetId = p.AssetId,
#                      Value = p.Value
#        }).Concat(Outputs.Select(p= > new
#        {
#            AssetId = p.AssetId,
#                      Value = -p.Value
#        })).GroupBy(p= > p.AssetId, (k, g) = > new
#        TransactionResult
#        {
#            AssetId = k,
#                      Amount = g.Sum(p= > p.Value)
#        }).Where(p= > p.Amount != Fixed8.Zero);


    def Serialize(self, writer):
        self.SerializeUnsigned(writer)
        writer.WriteSerializableArray(self.scripts)

    def SerializeUnsigned(self, writer):
        writer.WriteByte(self.Type)
        writer.WriteByte(self.Version)
        self.SerializeExclusiveData(writer)
        writer.WriteSerializableArray(self.Attributes)
        writer.WriteSerializableArray(self.inputs)
        writer.WriteSerializableArray(self.outputs)


    def SerializeExclusiveData(self, writer):
        # ReWrite in RegisterTransaction and IssueTransaction#
        pass


    def OnDeserialized(self):
        pass

    def ToJson(self):
        jsn = {}
        jsn["txid"] = self.HashToString()
        jsn["type"] = self.Type if type(self.Type) is int else int.from_bytes( self.Type, 'little')
        jsn["version"] = self.Version
        jsn["attributes"] = [attr.ToJson() for attr in self.Attributes]
        jsn["vout"] = [out.ToJson() for out in self.outputs]
        jsn["vin"] = [input.ToJson() for input in self.inputs]
        jsn["sys_fee"] = self.SystemFee().value
        jsn["net_fee"] = self.NetworkFee().value
        jsn["scripts"] = [script.ToJson() for script in self.scripts]
        return jsn


    def Verify(self, mempool):
        self.__log.debug("Verifying transaction: %s " % self.HashToString())
        for i in range(1, len(self.inputs)):
            j=0
            while j < i:
                j = j+1
                if self.inputs[i].PrevHash() == self.inputs[j].PrevHash() and self.inputs[i].PrevIndex() == self.inputs[j].PrevIndex():
                    return False
        self.__log.debug("Verified inputs 1")
        for tx in mempool:
            if tx is not self:
                for ip in self.inputs:
                    if ip in tx.inputs:
                        return False


        self.__log.debug("Verified inputs 2, checking double spend")

        if GetBlockchain().IsDoubleSpend(self):
            return False


        self.__log.debug("verifying outputs ...")
        for txOutput in self.outputs:
            asset = GetBlockchain().GetAssetState(txOutput.AssetId)

            if asset is None: return False

            if txOutput.Value % pow(10, 8 - asset.Precision) != 0:
                return False

        self.__log.debug("unimplemented after here ...")
        return True

        txResults = self.GetTransactionResults()

        if txResults is None: return False

        destroyedResults = []
        [destroyedResults.append(tx) for tx in txResults if tx.Amount==Fixed8(0)]
        numDestroyed = len(destroyedResults)
        if numDestroyed > 1:
            return False
        if numDestroyed == 1 and destroyedResults[0].AssetId != GetSystemCoin().Hash():
            return False
        if self.SystemFee() > Fixed8(0) and ( numDestroyed == 0 or destroyedResults[0].Amount < self.SystemFee()):
            return False

        issuedResults = []

        [issuedResults.append(tx) for tx in txResults if tx.Amount() < Fixed8(0)]

        if self.Type == TransactionType.MinerTransaction or self.Type == TransactionType.ClaimTransaction:
            for tx in issuedResults:
                if tx.AssetId != GetSystemCoin().Hash():
                    return False

        elif self.Type == TransactionType.IssueTransaction:
            for tx in issuedResults:
                if tx.AssetId != GetSystemCoin().Hash():
                    return False

        else:
            if len(issuedResults) > 0:
                return False


        usageECDH=0

        for attr in self.Attributes:
            if attr.Usage == TransactionAttributeUsage.ECDH02 or attr.Usage == TransactionAttributeUsage.ECDH03:
                usageECDH = usageECDH+1
                if usageECDH > 1:
                    return False

        return Helper.VerifyScripts(self)