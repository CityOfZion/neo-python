"""
Description:
    Transaction Basic Class
Usage:
    from neo.Core.Transaction import Transaction
"""
import sys
from itertools import groupby
import binascii
from neo.Core.UInt160 import UInt160
from neo.Blockchain import GetBlockchain
from neo.Core.TX.TransactionAttribute import TransactionAttributeUsage
from neo.Core.Fixed8 import Fixed8

from neo.Network.InventoryType import InventoryType
from neo.Network.Mixins import InventoryMixin
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.IO.Mixins import SerializableMixin
from neo.IO.MemoryStream import StreamManager
from neo.Core.IO.BinaryReader import BinaryReader
from neo.Core.Mixins import EquatableMixin
import neo.Core.Helper
from neo.Core.Witness import Witness
from neo.Core.UInt256 import UInt256
from neo.Core.AssetType import AssetType
from neo.Core.Size import Size as s
from neo.Core.Size import GetVarSize
from neo.Settings import settings
from neo.logging import log_manager
import neo.SmartContract.Helper as SCHelper

logger = log_manager.getLogger()


class TransactionResult(EquatableMixin):

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


class TransactionType:
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

    def Size(self):
        return self.Value.Size() + s.uint160 + s.uint256


class TransactionInput(SerializableMixin, EquatableMixin):
    """docstring for TransactionInput"""

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


class Transaction(InventoryMixin):
    Version = 0
    InventoryType = InventoryType.TX
    MAX_TX_ATTRIBUTES = 16
    MAX_TX_SIZE = 102400

    def __init__(self, inputs=None, outputs=None, attributes=None, scripts=None):
        """
        Create an instance.
        Args:
            inputs (list): of neo.Core.CoinReference.CoinReference.
            outputs (list): of neo.Core.TX.Transaction.TransactionOutput items.
            attributes (list): of neo.Core.TX.TransactionAttribute.
            scripts:
        """
        super(Transaction, self).__init__()
        self.inputs = [] if inputs is None else inputs
        self.outputs = [] if outputs is None else outputs
        self.Attributes = [] if attributes is None else attributes
        self.scripts = [] if scripts is None else scripts
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self._references = None
        self.Type = None
        self.raw_tx = False
        self.withdraw_hold = None
        self._network_fee = None
        self.__system_fee = None
        self.__hash = None
        self.__htbs = None
        self.__height = 0

    def __repr__(self):
        return f"<{self.__class__.__name__} at {hex(id(self))}> {self.Hash.ToString()}"

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
        return neo.Core.Helper.Helper.GetHashData(self)

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
        self._references = None

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
        if self._references is None:

            refs = {}

            # group by the input prevhash
            for hash, group in groupby(self.inputs, lambda x: x.PrevHash):

                tx, height = GetBlockchain().GetTransaction(hash.ToBytes())
                if tx is not None:
                    for input in group:
                        refs[input] = tx.outputs[input.PrevIndex]

            self._references = refs

        return self._references

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return s.uint8 + s.uint8 + GetVarSize(self.Attributes) + GetVarSize(self.inputs) + GetVarSize(self.outputs) + GetVarSize(self.Scripts)

    def Height(self):
        return self.__height

    def SystemFee(self):
        """
        Get the system fee.

        Returns:
            Fixed8: currently fixed to 0.
        """
        tx_name = TransactionType.ToName(self.Type)
        return Fixed8.FromDecimal(settings.ALL_FEES.get(tx_name, 0))

    def NetworkFee(self):
        """
        Get the network fee.

        Returns:
            Fixed8:
        """
        if self._network_fee is None:

            input = Fixed8(0)

            for coin_ref in self.References.values():
                if coin_ref.AssetId == GetBlockchain().SystemCoin().Hash:
                    input = input + coin_ref.Value

            output = Fixed8(0)

            for tx_output in self.outputs:
                if tx_output.AssetId == GetBlockchain().SystemCoin().Hash:
                    output = output + tx_output.Value

            self._network_fee = input - output - self.SystemFee()

        #            logger.info("Determined network fee to be %s " % (self.__network_fee.value))

        return self._network_fee

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

        self.scripts = reader.ReadSerializableArray('neo.Core.Witness.Witness')
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
        ttype = ord(reader.ReadByte())
        tx = None

        from neo.Core.TX.RegisterTransaction import RegisterTransaction
        from neo.Core.TX.IssueTransaction import IssueTransaction
        from neo.Core.TX.ClaimTransaction import ClaimTransaction
        from neo.Core.TX.MinerTransaction import MinerTransaction
        from neo.Core.TX.PublishTransaction import PublishTransaction
        from neo.Core.TX.InvocationTransaction import InvocationTransaction
        from neo.Core.TX.EnrollmentTransaction import EnrollmentTransaction
        from neo.Core.TX.StateTransaction import StateTransaction
        from neo.Core.TX.Transaction import ContractTransaction

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
        elif ttype == int.from_bytes(TransactionType.ContractTransaction, 'little'):
            tx = ContractTransaction()
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
        txtype = ord(reader.ReadByte())
        if txtype != int.from_bytes(self.Type, 'little'):
            raise Exception('incorrect type {}, wanted {}'.format(txtype, int.from_bytes(self.Type, 'little')))
        self.DeserializeUnsignedWithoutType(reader)

    def DeserializeUnsignedWithoutType(self, reader):
        """
        Deserialize object without reading transaction type data.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Version = ord(reader.ReadByte())
        self.DeserializeExclusiveData(reader)
        self.Attributes = reader.ReadSerializableArray('neo.Core.TX.TransactionAttribute.TransactionAttribute',
                                                       max=self.MAX_TX_ATTRIBUTES)
        self.inputs = reader.ReadSerializableArray('neo.Core.CoinReference.CoinReference')
        self.outputs = reader.ReadSerializableArray('neo.Core.TX.Transaction.TransactionOutput')

    def Equals(self, other):
        if other is None or other is not self or not isinstance(other, Transaction):
            return False
        return self.Hash == other.Hash

    def __eq__(self, other):
        return self.Equals(other)

    def ToArray(self):
        """
        Get the byte data of self.

        Returns:
            bytes:
        """
        return neo.Core.Helper.Helper.ToArray(self)

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
        jsn["size"] = self.Size()
        jsn["type"] = TransactionType.ToName(self.Type)
        jsn["version"] = self.Version
        jsn["attributes"] = [attr.ToJson() for attr in self.Attributes]
        jsn["vout"] = [out.ToJson(i) for i, out in enumerate(self.outputs)]
        jsn["vin"] = [input.ToJson() for input in self.inputs]
        jsn["sys_fee"] = self.SystemFee().ToNeoJsonString()
        jsn["net_fee"] = self.NetworkFee().ToNeoJsonString()
        jsn["scripts"] = [script.ToJson() for script in self.scripts]
        return jsn

    def Verify(self, snapshot, mempool):
        """
        Verify the transaction.

        Args:
            mempool:

        Returns:
            bool: True if verified. False otherwise.
        """
        logger.debug("Verifying transaction: %s " % self.Hash.ToBytes())

        # SimplePolicyPlugin
        if self.Size() > self.MAX_TX_SIZE:
            logger.debug(f'Maximum transaction size exceeded: {self.Size()} > {self.MAX_TX_SIZE}')
            return False
        fee = self.NetworkFee()
        if self.Size() > settings.MAX_FREE_TX_SIZE and not self.Type == b'\x02':  # Claim Transactions are High Priority
            req_fee = Fixed8.FromDecimal(settings.FEE_PER_EXTRA_BYTE * (self.Size() - settings.MAX_FREE_TX_SIZE))
            if req_fee < settings.LOW_PRIORITY_THRESHOLD:
                req_fee = settings.LOW_PRIORITY_THRESHOLD
            if fee < req_fee:
                logger.debug(f'The tx size ({self.Size()}) exceeds the max free tx size ({settings.MAX_FREE_TX_SIZE}).\nA network fee of {req_fee.ToString()} GAS is required.')
                return False

        return SCHelper.Helper.VerifyWitnesses(self, snapshot)
        # return neo.Core.Helper.Helper.VerifyScripts(self)

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

    def GetScriptHashesForVerifying(self, snapshot=None):
        """
        Get a list of script hashes for verifying transactions.

        Raises:
            Exception: if there are no valid assets in the transaction.
            ValueError: if a snapshot object is not provided for regular transactions. RawTx is exempt from this check.

        Returns:
            list: of UInt160 type script hashes.
        """
        if snapshot is None and not self.raw_tx:
            raise ValueError("Snapshot cannot be None for regular transaction types")

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
            if self.raw_tx:
                asset = neo.Core.Helper.Helper.StaticAssetState(key)
            else:
                asset = snapshot.Assets.TryGet(key.ToBytes())
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
