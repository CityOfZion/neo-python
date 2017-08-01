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
import sys
import json
from neo.Core.Witness import Witness
from autologging import logged

class TransactionResult():
    AssetId=None
    Amount=0

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

@logged
class TransactionOutput(SerializableMixin):


    Value = None
    ScriptHash = None
    AssetId = None

    """docstring for TransactionOutput"""
    def __init__(self, AssetId=None, Value=None, ScriptHash=None):
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Value
        self.ScriptHash = ScriptHash

    def Serialize(self, writer):
        writer.WriteUInt256(self.AssetId)
        writer.WriteDouble(float(self.Value))
        writer.WriteUInt160(self.ScriptHash)

    def Deserialize(self, reader):
        self.AssetId = reader.ReadUInt256()
        self.Value = reader.ReadDouble()
        self.ScriptHash = reader.ReadUInt160()


@logged
class TransactionInput(SerializableMixin):
    """docstring for TransactionInput"""

    PrevHash=None
    PrevIndex=None

    def __init__(self, prevHash, prevIndex):
        super(TransactionInput, self).__init__()
        self.PrevHash = prevHash
        self.PrevIndex = int(prevIndex)

    def Serialize(self, writer):
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Deserialize(self, reader):
        self.PrevHash = reader.ReadUInt256()
        self.PrevIndex = reader.ReadUInt16()

    def ToString(self):
        # to string
        return self.PrevHash + ":" + self.PrevIndex


class Transaction(Inventory, InventoryMixin):


    Type = None

    Version = None

    Attributes = []

    inputs = []

    outputs = []

    scripts = []

    systemFee = Fixed8(0)

    InventoryType = InventoryType.TX

    __network_fee = -1

    __hash = None

    __height = 0

    __references = {}


    """docstring for Transaction"""
    def __init__(self, inputs=[], outputs=[], attributes = [], scripts=[] ):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.Attributes= attributes
        self.scripts = scripts
        self.Type = None
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.systemFee = self.SystemFee()


    def Hash(self):
        if not self.__hash:
            hashdata = Helper.GetHashData(self)
            ba = bytearray(binascii.unhexlify(hashdata))
            self.__hash = Crypto.Hash256( ba )
        return self.__hash

    def HashHex(self):
        return binascii.hexlify(self.Hash())


    def HashToString(self):
        ba = bytearray(self.Hash())
        ba.reverse()
        return binascii.hexlify(ba)

    def NetworkFee(self):
        if self.__network_fee == -Fixed8.Satoshi():
#            Fixed8 input = References.Values.Where(p= > p.AssetId.Equals(.SystemCoin.Hash)).Sum(p= > p.Value);
#            Fixed8 output = Outputs.Where(p= > p.AssetId.Equals(Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
#            _network_fee = input - output - SystemFee;
            pass

        return self.__network_fee


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

#        if (Settings.Default.SystemFee.ContainsKey(Type))
#            return Settings.Default.SystemFee[Type];
        return Fixed8(0)


    def Deserialize(self, reader):

        self.DeserializeUnsigned(reader)

        self.scripts = reader.ReadSerializableArray()
        self.OnDeserialized()


    def DeserializeExclusiveData(self, reader):
        pass


    @staticmethod
    def DeserializeFromBufer(buffer, offset=0):
        mstream = MemoryStream(buffer, offset)
        reader = BinaryReader(mstream)
        return Transaction.DeserializeFrom(reader)

    @staticmethod
    def DeserializeFrom(reader):
        ttype = reader.ReadByte()
        tx = None

        from neo.Core.TX.RegisterTransaction import RegisterTransaction
        from neo.Core.TX.IssueTransaction import IssueTransaction
        from neo.Core.TX.ClaimTransaction import ClaimTransaction
        from neo.Core.TX.MinerTransaction import MinerTransaction

        if ttype == int.from_bytes( TransactionType.RegisterTransaction, 'little'):
            tx = RegisterTransaction()
        elif ttype == int.from_bytes( TransactionType.MinerTransaction, 'little'):
            tx = MinerTransaction()
        elif ttype == int.from_bytes( TransactionType.IssueTransaction, 'little'):
            tx = IssueTransaction()
        elif ttype == int.from_bytes( TransactionType.ClaimTransaction, 'little'):
            tx = ClaimTransaction()

        tx.DeserializeUnsignedWithoutType(reader)


        try:
            witness = Witness()
            witness.Deserialize(reader)
            tx.scripts = [witness]
        except Exception as e:
            pass


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
        self.inputs = [CoinReference(ref) for ref in reader.ReadSerializableArray('neo.Core.CoinReference.CoinReference')]
        self.outputs = [TransactionOutput(ref) for ref in reader.ReadSerializableArray('neo.Core.TX.Transaction.TransactionOutput')]


    def Equals(self, other):
        if other is None or other is not self:
            return False
        return self.Hash() == other.Hash()

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
        jsn["txid"] = self.Hash()
        jsn["size"] = self.Size()
        jsn["type"] = self.Type
        jsn["version"] = self.Version
        jsn["attributes"] = [attr.ToJson() for attr in self.Attributes]
        jsn["vout"] = [out.ToJson() for out in self.outputs]
        jsn["sys_fee"] = self.SystemFee()
        jsn["net_fee"] = self.NetworkFee()
        jsn["scripts"] = [script.ToJson() for script in self.scripts]

        return json.dumps(jsn)


    def Verify(self, mempool):
        for i in range(1, len(self.inputs)):
            j=0
            while j < i:
                j = j+1
                if self.inputs[i].PrevHash() == self.inputs[j].PrevHash() and self.inputs[i].PrevIndex() == self.inputs[j].PrevIndex():
                    return False

        for tx in mempool:
            if tx is not self:
                for ip in self.inputs:
                    if ip in tx.inputs:
                        return False

        if GetBlockchain().IsDoubleSpend(self):
            return False

        for txOutput in self.outputs:
            asset = GetBlockchain().GetAssetState(txOutput.AssetId)

            if asset is None: return False

            if txOutput.Value % pow(10, 8 - asset.Precision) != 0:
                return False

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