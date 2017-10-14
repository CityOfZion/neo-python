# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from neo.Core.Transaction import Transaction
"""

from neo.Blockchain import *
from neo.Core.TX.TransactionAttribute import *
from neo.Core.CoinReference import CoinReference
from neo.Fixed8 import Fixed8
from neo.Network.Inventory import Inventory
from neo.Network.InventoryType import InventoryType
from neo.Network.Mixins import InventoryMixin
from neo.Cryptography.Crypto import *
from neo.IO.Mixins import SerializableMixin
from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryReader import BinaryReader
from neo.Core.Helper import Helper
from neo.Core.Witness import Witness
from autologging import logged
from neo.UInt256 import UInt256

import sys
from itertools import groupby
from neo.Core.AssetType import AssetType
import pdb

class TransactionResult():
    AssetId=None
    Amount=Fixed8(0)

    def __init__(self, asset_id, amount):
        self.AssetId = asset_id
        self.Amount = amount

    def ToString(self):
        return "%s -> %s " % (self.AssetId.ToString(), self.Amount.value)

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
    ScriptHash = None
    AssetId = None

    """docstring for TransactionOutput"""
    def __init__(self, AssetId=None, Value=None, script_hash=None):
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Value
        self.ScriptHash = script_hash

#        if self.ScriptHash is None:
#            raise Exception("Script hash is required!!!!!!!!")

    @property
    def Address(self):
        return Crypto.ToAddress(self.ScriptHash)

    @property
    def AddressBytes(self):
        return bytes(self.Address, encoding='utf-8')

    def Serialize(self, writer):
        writer.WriteUInt256(self.AssetId)
        writer.WriteFixed8(self.Value)
        writer.WriteUInt160(self.ScriptHash)

    def Deserialize(self, reader):
        self.AssetId = reader.ReadUInt256()
        self.Value = reader.ReadFixed8()
        self.ScriptHash = reader.ReadUInt160()
        if self.ScriptHash is None:
            raise Exception("Script hash is required from deserialize!!!!!!!!")


    def ToJson(self):
        return {
            'AssetId': self.AssetId.ToString(),
            'Value': self.Value.value,
            'ScriptHash': self.Address
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
        self.PrevHash = reader.ReadUInt256()
        self.PrevIndex = reader.ReadUInt16()

    def ToString(self):
        # to string
        return self.PrevHash + ":" + self.PrevIndex

    def ToJson(self):
        return {
            'PrevHash': self.PrevHash.ToString(),
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

    __system_fee =  None
    __network_fee = None

    InventoryType = InventoryType.TX


    __hash = None
    __htbs = None

    __height = 0

    __references = None

    MAX_TX_ATTRIBUTES=16

    """docstring for Transaction"""
    def __init__(self, inputs=[], outputs=[], attributes = [], scripts=[] ):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.Attributes= attributes
        self.scripts = scripts
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.__references = None

    @property
    def Hash(self):
        if not self.__hash:
            ba = bytearray(binascii.unhexlify(self.GetHashData()))
            hash = Crypto.Hash256(ba)
            self.__hash = UInt256(data=hash)
        return self.__hash


    def GetHashData(self):
        return Helper.GetHashData(self)


    def GetMessage(self):
        return self.GetHashData()


    def getAllInputs(self):
        return self.inputs

    def ResetReferences(self):
        self.__references = None

    @property
    def Scripts(self):
        return self.scripts

    @property
    def References(self):

        if self.__references is None:

            refs = {}

            #group by the input prevhash
            for hash, group in groupby(self.inputs, lambda x: x.PrevHash):

                tx,height = GetBlockchain().GetTransaction(hash.ToBytes())
                if tx is not None:
                    for input in group:
                        refs[input] = tx.outputs[input.PrevIndex]

            self.__references = refs

        return self.__references



    def Size(self):
        return sys.getsizeof(self.Type) + sys.getsizeof(0) \
               + sys.getsizeof(self.Attributes) + sys.getsizeof(self.inputs) + \
                    sys.getsizeof(self.outputs) + sys.getsizeof(self.scripts)


    def Height(self):
        return self.__height

    def SystemFee(self):
        return Fixed8(0)

    def NetworkFee(self):

        if self.__network_fee is None:

            input = Fixed8(0)

            for coin_ref in self.References.values():
                if coin_ref.AssetId == GetBlockchain().SystemCoin().Hash:
                    input = input + coin_ref.Value

            output = Fixed8(0)

            for tx_output in self.outputs:
                if tx_output.AssetId == GetBlockchain().SystemCoin().Hash:
                    output = output + tx_output.Value

            self.__network_fee = input - output - self.SystemFee()

#            print("Determined network fee to be %s " % (self.__network_fee.value))

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
        mstream = StreamManager.GetStream(buffer)
        reader = BinaryReader(mstream)
        tx = Transaction.DeserializeFrom(reader)

        StreamManager.ReleaseStream(mstream)
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

                tx.scripts.append(witness)

        tx.OnDeserialized()

        return tx

    def DeserializeUnsigned(self, reader):
        if reader.ReadByte() != self.Type:
            raise Exception('incorrect type')
        self.DeserializeUnsignedWithoutType(reader)

    def DeserializeUnsignedWithoutType(self,reader):
        self.Version = reader.ReadByte()
        self.DeserializeExclusiveData(reader)
        self.Attributes = reader.ReadSerializableArray('neo.Core.TX.TransactionAttribute.TransactionAttribute',max=self.MAX_TX_ATTRIBUTES)
        self.inputs = reader.ReadSerializableArray( 'neo.Core.CoinReference.CoinReference')
        self.outputs = reader.ReadSerializableArray('neo.Core.TX.Transaction.TransactionOutput')

    def Equals(self, other):
        if other is None or other is not self:
            return False
        return self.Hash == other.Hash

    def ToArray(self):
        return Helper.ToArray(self)

    def Serialize(self, writer):
        self.SerializeUnsigned(writer)
        writer.WriteSerializableArray(self.scripts)

    def SerializeUnsigned(self, writer):
        writer.WriteByte(self.Type)
        writer.WriteByte(self.Version)
        self.SerializeExclusiveData(writer)

        if len(self.Attributes) > self.MAX_TX_ATTRIBUTES:

            raise Exception("Cannot have more than %s transaction attributes" % self.MAX_TX_ATTRIBUTES)

        writer.WriteSerializableArray(self.Attributes)
        writer.WriteSerializableArray(self.inputs)
        writer.WriteSerializableArray(self.outputs)


    def SerializeExclusiveData(self, writer):
        pass


    def OnDeserialized(self):
        pass

    def ToJson(self):
        jsn = {}
        jsn["txid"] = self.Hash.ToString()
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
        self.__log.debug("Verifying transaction: %s " % self.Hash.ToBytes())


        return Helper.VerifyScripts(self)

#        print("return true for now ...")
#        return True

#        for i in range(1, len(self.inputs)):
#            j=0
#            while j < i:
#                j = j+1
#                if self.inputs[i].PrevHash == self.inputs[j].PrevHash and self.inputs[i].PrevIndex() == self.inputs[j].PrevIndex():
#                    return False
##        self.__log.debug("Verified inputs 1")
#       for tx in mempool:
#           if tx is not self:
#               for ip in self.inputs:
#                   if ip in tx.inputs:
#                       return False
#
#        self.__log.debug("Verified inputs 2, checking double spend")
#
#        if GetBlockchain().IsDoubleSpend(self):
#            return False
#
#        self.__log.debug("verifying outputs ...")
#        for txOutput in self.outputs:
#            asset = GetBlockchain().GetAssetState(txOutput.AssetId)
#
#            if asset is None: return False
#
#            if txOutput.Value % pow(10, 8 - asset.Precision) != 0:
#                return False
#
#        self.__log.debug("unimplemented after here ...")
#        return True
#        txResults = self.GetTransactionResults()
#
#        if txResults is None: return False
#
#        destroyedResults = []
#        [destroyedResults.append(tx) for tx in txResults if tx.Amount==Fixed8(0)]
#        numDestroyed = len(destroyedResults)
#        if numDestroyed > 1:
#            return False
#        if numDestroyed == 1 and destroyedResults[0].AssetId != GetSystemCoin().Hash:
#            return False
#        if self.SystemFee() > Fixed8(0) and ( numDestroyed == 0 or destroyedResults[0].Amount < self.SystemFee()):
#            return False
#
#        issuedResults = []
#
#        [issuedResults.append(tx) for tx in txResults if tx.Amount() < Fixed8(0)]
#
#        if self.Type == TransactionType.MinerTransaction or self.Type == TransactionType.ClaimTransaction:
#            for tx in issuedResults:
#                if tx.AssetId != GetSystemCoin().Hash:
#                    return False
#
#        elif self.Type == TransactionType.IssueTransaction:
#            for tx in issuedResults:
#                if tx.AssetId != GetSystemCoin().Hash:
#                    return False
#
#        else:
#            if len(issuedResults) > 0:
#                return False
#
#        usageECDH=0
#
#        for attr in self.Attributes:
#            if attr.Usage == TransactionAttributeUsage.ECDH02 or attr.Usage == TransactionAttributeUsage.ECDH03:
#                usageECDH = usageECDH+1
#                if usageECDH > 1:
#                    return False
#



    def GetScriptHashesForVerifying(self):


        if not self.References and len(self.Attributes) < 1:
            return []

        hashes = set()
        for coinref,output in self.References.items():
            hashes.add(output.ScriptHash)

        for attr in self.Attributes:
            if attr.Usage == TransactionAttributeUsage.Script:
                if type(attr.Data) is UInt160:
                    hashes.add(attr.Data)
                else:
                    hashes.add( UInt160(data=attr.Data))

        for key, group in groupby(self.outputs, lambda p: p.AssetId):
            asset = GetBlockchain().GetAssetState(key.ToBytes())
            if asset is None:
                raise Exception("Invalid operation")

            if asset.AssetType == AssetType.DutyFlag:
                for p in group:
                    hashes.add(p.ScriptHash)

        hashlist = list(hashes)
        hashlist.sort()
        return hashlist


    def GetTransactionResults(self):
        if self.References is None: return None

        results = []
        realresults = []
        for ref_output in self.References.values():
            results.append(TransactionResult(ref_output.AssetId, ref_output.Value))

        for output in self.outputs:
            results.append(TransactionResult(output.AssetId, output.Value * Fixed8(-1)))

        for key, group in groupby(results, lambda x: x.AssetId):
            sum=Fixed8(0)
            for item in group:
                sum = sum + item.Amount

            if sum != Fixed8.Zero():

                realresults.append( TransactionResult(key, sum))

        return realresults


class ContractTransaction(Transaction):
    def __init__(self, *args, **kwargs):
        super(ContractTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.ContractTransaction
