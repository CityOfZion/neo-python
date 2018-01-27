# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from neo.Core.Transaction import Transaction
"""
from itertools import groupby
from neo.Blockchain import *
from neo.Core.TX.TransactionAttribute import *
from neocore.Fixed8 import Fixed8
from neo.Network.Inventory import Inventory
from neo.Network.InventoryType import InventoryType
from neo.Network.Mixins import InventoryMixin
from neocore.Cryptography.Crypto import *
from neocore.IO.Mixins import SerializableMixin
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neo.Core.Mixins import EquatableMixin
from neo.Core.Helper import Helper
from neo.Core.Witness import Witness
from neocore.UInt256 import UInt256
from neo.Core.AssetType import AssetType
import inspect


class TransactionResult(EquatableMixin):
    AssetId = None
    Amount = Fixed8(0)

    def __init__(self, asset_id, amount):
        """
        Create an instance.

        Args:
            asset_id (UInt256):
            amount (Fixed8):
        """
        self.AssetId = asset_id
        self.Amount = amount

    def ToString(self):
        """
        Get a string representation of the object.

        Returns:
            str:
        """
        return "%s -> %s " % (self.AssetId.ToString(), self.Amount.value)


class TransactionType(object):
    MinerTransaction = b'\x00'
    IssueTransaction = b'\x01'
    ClaimTransaction = b'\x02'
    EnrollmentTransaction = b'\x20'
    VotingTransaction = b'\x24'
    RegisterTransaction = b'\x40'
    ContractTransaction = b'\x80'
    StateTransaction = b'\x90'
    AgencyTransaction = b'\xb0'
    PublishTransaction = b'\xd0'
    InvocationTransaction = b'\xd1'

    @staticmethod
    def ToName(value):
        if isinstance(value, int):
            value = value.to_bytes(1, 'little')
        for key, item in TransactionType.__dict__.items():
            if value == item:
                return key
        return None


class TransactionOutput(SerializableMixin, EquatableMixin):
    Value = None  # should be fixed 8
    ScriptHash = None
    AssetId = None

    """docstring for TransactionOutput"""

    def __init__(self, AssetId=None, Value=None, script_hash=None):
        """
        Create an instance.

        Args:
            AssetId (UInt256):
            Value (Fixed8):
            script_hash (UInt160):
        """
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Value
        self.ScriptHash = script_hash

    #        if self.ScriptHash is None:
    #            raise Exception("Script hash is required!!!!!!!!")

    @property
    def Address(self):
        """
        Get the public address of the transaction.

        Returns:
            str: base58 encoded string representing the address.
        """
        return Crypto.ToAddress(self.ScriptHash)

    @property
    def AddressBytes(self):
        """
        Get the public address of the transaction.

        Returns:
            bytes: base58 encoded address.
        """
        return bytes(self.Address, encoding='utf-8')

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt256(self.AssetId)
        writer.WriteFixed8(self.Value)
        writer.WriteUInt160(self.ScriptHash)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.AssetId = reader.ReadUInt256()
        self.Value = reader.ReadFixed8()
        self.ScriptHash = reader.ReadUInt160()
        if self.ScriptHash is None:
            raise Exception("Script hash is required from deserialize!!!!!!!!")

    def ToJson(self, index):
        """
        Convert object members to a dictionary that can be parsed as JSON.
        Args:
            index (int): The index of the output in a transaction

        Returns:
             dict:
        """
        return {
            'n': index,
            'asset': self.AssetId.To0xString(),
            'value': self.Value.ToNeoJsonString(),
            'address': self.Address
        }


class TransactionInput(SerializableMixin, EquatableMixin):
    """docstring for TransactionInput"""

    PrevHash = None
    PrevIndex = None

    def __init__(self, prevHash=None, prevIndex=None):
        """
        Create an instance.
        Args:
            prevHash (UInt256):
            prevIndex (int):
        """
        super(TransactionInput, self).__init__()
        self.PrevHash = prevHash
        self.PrevIndex = prevIndex

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.PrevHash = reader.ReadUInt256()
        self.PrevIndex = reader.ReadUInt16()

    def ToString(self):
        """
        Get the string representation of the object.

        Returns:
            str: PrevHash:PrevIndex
        """
        return self.PrevHash + ":" + self.PrevIndex

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        return {
            'PrevHash': self.PrevHash.To0xString(),
            'PrevIndex': self.PrevIndex
        }


class Transaction(Inventory, InventoryMixin):
    Type = None

    Version = 0

    Attributes = []

    inputs = []

    outputs = []

    scripts = []

    __system_fee = None
    __network_fee = None

    InventoryType = InventoryType.TX

    __hash = None
    __htbs = None

    __height = 0

    __references = None

    MAX_TX_ATTRIBUTES = 16

    withdraw_hold = None

    """docstring for Transaction"""

    def __init__(self, inputs=[], outputs=[], attributes=[], scripts=[]):
        """
        Create an instance.
        Args:
            inputs (list): of neo.Core.CoinReference.CoinReference.
            outputs (list): of neo.Core.TX.Transaction.TransactionOutput items.
            attributes (list): of neo.Core.TX.TransactionAttribute.
            scripts:
        """
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.Attributes = attributes
        self.scripts = scripts
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.__references = None

    @property
    def Hash(self):
        """
        Get the hash of the transaction.

        Returns:
            UInt256:
        """
        if not self.__hash:
            ba = bytearray(binascii.unhexlify(self.GetHashData()))
            hash = Crypto.Hash256(ba)
            self.__hash = UInt256(data=hash)
        return self.__hash

    def GetHashData(self):
        """
        Get the data used for hashing.

        Returns:
            bytes:
        """
        return Helper.GetHashData(self)

    def GetMessage(self):
        """
        Get the data used for hashing.

        Returns:
            bytes:
        """
        return self.GetHashData()

    def getAllInputs(self):
        """
        Get the inputs.

        Returns:
            list:
        """
        return self.inputs

    def ResetReferences(self):
        """Reset local stored references."""
        self.__references = None

    def ResetHashData(self):
        """Reset local stored hash data."""
        self.__hash = None

    @property
    def Scripts(self):
        """
        Get the scripts

        Returns:
            list:
        """
        return self.scripts

    @property
    def References(self):
        """
        Get all references.

        Returns:
            dict:
                Key (UInt256): input PrevHash
                Value (TransactionOutput): object.
        """
        if self.__references is None:

            refs = {}

            # group by the input prevhash
            for hash, group in groupby(self.inputs, lambda x: x.PrevHash):

                tx, height = GetBlockchain().GetTransaction(hash.ToBytes())
                if tx is not None:
                    for input in group:
                        refs[input] = tx.outputs[input.PrevIndex]

            self.__references = refs

        return self.__references

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        len_attributes = sys.getsizeof(self.Attributes)
        len_inputs = sys.getsizeof(self.inputs)
        len_outputs = sys.getsizeof(self.outputs)
        len_scripts = sys.getsizeof(self.scripts)
        return sys.getsizeof(self.Type) + sys.getsizeof(0) + len_attributes + len_inputs + len_outputs + len_scripts

    def Height(self):
        return self.__height

    def SystemFee(self):
        """
        Get the system fee.

        Returns:
            Fixed8: currently fixed to 0.
        """
        return Fixed8(0)

    def NetworkFee(self):
        """
        Get the network fee.

        Returns:
            Fixed8:
        """
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

        #            logger.info("Determined network fee to be %s " % (self.__network_fee.value))

        return self.__network_fee

    #        if self.__network_fee == Fixed8.Satoshi():
    #            Fixed8 input = References.Values.Where(p= > p.AssetId.Equals(.SystemCoin.Hash)).Sum(p= > p.Value);
    #            Fixed8 output = Outputs.Where(p= > p.AssetId.Equals(Blockchain.SystemCoin.Hash)).Sum(p= > p.Value);
    #            _network_fee = input - output - SystemFee;
    #            pass

    #        return self.__network_fee

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.DeserializeUnsigned(reader)

        self.scripts = reader.ReadSerializableArray()
        self.OnDeserialized()

    def DeserializeExclusiveData(self, reader):
        pass

    @staticmethod
    def DeserializeFromBufer(buffer, offset=0):
        """
        Deserialize object instance from the specified buffer.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.
            offset: UNUSED

        Returns:
            Transaction:
        """
        mstream = StreamManager.GetStream(buffer)
        reader = BinaryReader(mstream)
        tx = Transaction.DeserializeFrom(reader)

        StreamManager.ReleaseStream(mstream)
        return tx

    @staticmethod
    def DeserializeFrom(reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):

        Returns:
            Transaction:
        """
        ttype = reader.ReadByte()
        tx = None

        from neo.Core.TX.RegisterTransaction import RegisterTransaction
        from neo.Core.TX.IssueTransaction import IssueTransaction
        from neo.Core.TX.ClaimTransaction import ClaimTransaction
        from neo.Core.TX.MinerTransaction import MinerTransaction
        from neo.Core.TX.PublishTransaction import PublishTransaction
        from neo.Core.TX.InvocationTransaction import InvocationTransaction
        from neo.Core.TX.EnrollmentTransaction import EnrollmentTransaction
        from neo.Core.TX.StateTransaction import StateTransaction

        if ttype == int.from_bytes(TransactionType.RegisterTransaction, 'little'):
            tx = RegisterTransaction()
        elif ttype == int.from_bytes(TransactionType.MinerTransaction, 'little'):
            tx = MinerTransaction()
        elif ttype == int.from_bytes(TransactionType.IssueTransaction, 'little'):
            tx = IssueTransaction()
        elif ttype == int.from_bytes(TransactionType.ClaimTransaction, 'little'):
            tx = ClaimTransaction()
        elif ttype == int.from_bytes(TransactionType.PublishTransaction, 'little'):
            tx = PublishTransaction()
        elif ttype == int.from_bytes(TransactionType.InvocationTransaction, 'little'):
            tx = InvocationTransaction()
        elif ttype == int.from_bytes(TransactionType.EnrollmentTransaction, 'little'):
            tx = EnrollmentTransaction()
        elif ttype == int.from_bytes(TransactionType.StateTransaction, 'little'):
            tx = StateTransaction()
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
        """
        Deserialize object.

        Args:
            reader (neo.IO.BinaryReader):

        Raises:
            Exception: if transaction type is incorrect.
        """
        txtype = reader.ReadByte()
        if txtype != int.from_bytes(self.Type, 'little'):
            raise Exception('incorrect type {}, wanted {}'.format(txtype, int.from_bytes(self.Type, 'little')))
        self.DeserializeUnsignedWithoutType(reader)

    def DeserializeUnsignedWithoutType(self, reader):
        """
        Deserialize object without reading transaction type data.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Version = reader.ReadByte()
        self.DeserializeExclusiveData(reader)
        self.Attributes = reader.ReadSerializableArray('neo.Core.TX.TransactionAttribute.TransactionAttribute',
                                                       max=self.MAX_TX_ATTRIBUTES)
        self.inputs = reader.ReadSerializableArray('neo.Core.CoinReference.CoinReference')
        self.outputs = reader.ReadSerializableArray('neo.Core.TX.Transaction.TransactionOutput')

    def Equals(self, other):
        if other is None or other is not self:
            return False
        return self.Hash == other.Hash

    def ToArray(self):
        """
        Get the byte data of self.

        Returns:
            bytes:
        """
        return Helper.ToArray(self)

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        self.SerializeUnsigned(writer)
        writer.WriteSerializableArray(self.scripts)

    def SerializeUnsigned(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
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
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        jsn = {}
        jsn["txid"] = self.Hash.To0xString()
        jsn["type"] = TransactionType.ToName(self.Type)
        jsn["version"] = self.Version
        jsn["attributes"] = [attr.ToJson() for attr in self.Attributes]
        jsn["vout"] = [out.ToJson(i) for i, out in enumerate(self.outputs)]
        jsn["vin"] = [input.ToJson() for input in self.inputs]
        jsn["sys_fee"] = self.SystemFee().ToNeoJsonString()
        jsn["net_fee"] = self.NetworkFee().ToNeoJsonString()
        jsn["scripts"] = [script.ToJson() for script in self.scripts]
        return jsn

    def Verify(self, mempool):
        """
        Verify the transaction.

        Args:
            mempool:

        Returns:
            bool: True if verified. False otherwise.
        """
        logger.info("Verifying transaction: %s " % self.Hash.ToBytes())

        return Helper.VerifyScripts(self)

    #        logger.info("return true for now ...")
    #        return True

    #        for i in range(1, len(self.inputs)):
    #            j=0
    #            while j < i:
    #                j = j+1
    #                if self.inputs[i].PrevHash == self.inputs[j].PrevHash and self.inputs[i].PrevIndex() == self.inputs[j].PrevIndex():
    #                    return False
    #        logger.info("Verified inputs 1")
    #       for tx in mempool:
    #           if tx is not self:
    #               for ip in self.inputs:
    #                   if ip in tx.inputs:
    #                       return False
    #
    #        logger.info("Verified inputs 2, checking double spend")
    #
    #        if GetBlockchain().IsDoubleSpend(self):
    #            return False
    #
    #        logger.info("verifying outputs ...")
    #        for txOutput in self.outputs:
    #            asset = GetBlockchain().GetAssetState(txOutput.AssetId)
    #
    #            if asset is None: return False
    #
    #            if txOutput.Value % pow(10, 8 - asset.Precision) != 0:
    #                return False
    #
    #        logger.info("unimplemented after here ...")
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
        """
        Get a list of script hashes for verifying transactions.

        Raises:
            Exception: if there are no valid assets in the transaction.

        Returns:
            list: of UInt160 type script hashes.
        """
        if not self.References and len(self.Attributes) < 1:
            return []

        hashes = set()
        for coinref, output in self.References.items():
            hashes.add(output.ScriptHash)

        for attr in self.Attributes:
            if attr.Usage == TransactionAttributeUsage.Script:
                if type(attr.Data) is UInt160:
                    hashes.add(attr.Data)
                else:
                    hashes.add(UInt160(data=attr.Data))

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
        """
        Get the execution results of the transaction.

        Returns:
            None: if the transaction has no references.
            list: of TransactionResult objects.
        """
        if self.References is None:
            return None

        results = []
        realresults = []
        for ref_output in self.References.values():
            results.append(TransactionResult(ref_output.AssetId, ref_output.Value))

        for output in self.outputs:
            results.append(TransactionResult(output.AssetId, output.Value * Fixed8(-1)))

        for key, group in groupby(results, lambda x: x.AssetId):
            sum = Fixed8(0)
            for item in group:
                sum = sum + item.Amount

            if sum != Fixed8.Zero():
                realresults.append(TransactionResult(key, sum))

        return realresults


class ContractTransaction(Transaction):
    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(ContractTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.ContractTransaction
