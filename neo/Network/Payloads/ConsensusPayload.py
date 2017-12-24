from neo.IO.Mixins import SerializableMixin
from neo.Cryptography.Helper import *
from neo.Core.Helper import Helper
from neo.Network.InventoryType import InventoryType
from neo.Core.Blockchain import Blockchain
from neo.Wallets.VerificationContract import VerificationContract
from neo.Core.Witness import Witness
from neo.UInt256 import UInt256


class InvalidOperationException(Exception):
    pass


class ConsensusPayload(SerializableMixin):
    InventoryType = InventoryType.Consensus
    Version = 0
    PrevHash = None  # uint256
    BlockIndex = 0
    ValidatorIndex = 0
    Timestamp = 0
    Data = []
    Script = None  # Witness

    _hash = None

    def __init__(self, version=0, prevHash=UInt256(), blockIndex=0, validatorIndex=0, timestamp=0, data=[]):
        """
        Create an instance.

        Args:
            version (int):
            prevHash (UInt256):
            blockIndex (int):
            validatorIndex (int):
            timestamp (int):

        """
        self.Version = version
        self.PrevHash = prevHash  # must be UInt256 type
        self.BlockIndex = blockIndex
        self.ValidatorIndex = validatorIndex
        self.Timestamp = timestamp  # must be int
        self.Data = data

    @property
    def Hash(self):
        """
        Get the hash value of the payload.

        Returns:
            UInt256: containing the hash of the data.
        """
        if not self._hash:
            d = Helper.GetHashData(self)
            real_bytes = bytes.fromhex(d.decode('utf8'))
            # DO NOT use Helper.double_sha256() or Helper.bin_dbl_sha256() they either expect to operate on hexstrings encapsulated in a bytes object or return string data
            # Doing so leads to a wrong hash calculation
            h = hashlib.sha256()
            h2 = hashlib.sha256()

            h.update(real_bytes)
            h2.update(h.digest())
            self._hash = UInt256(data=h2.digest())
        return self._hash

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        from neo.IO.Helper import Helper as IOHelper
        size_of_uint = 4
        size_of_ushort = 2
        return size_of_uint + self.PrevHash.Size + size_of_uint + size_of_ushort + size_of_uint + IOHelper.GetVarSize(
            self.Data) + 1 + self.Script.Size()

    def GetMessage(self):
        """
        Get the hash data of the payload. Same result as GetHashData().

        Returns:
            bytes: a hexstring encapsulated in a bytes() object.
        """
        return Helper.GetHashData(self)

    def GetScriptHashesForVerifying(self):
        """
            Get own ScriptHash from the validators list for validation.

            Returns:
                list: containing one UInt160() ScriptHash .
        """
        # Can never be True, because Blockchain.Default() in neo-python will either get or create an instance. Leaving it in for reference.
        # if Blockchain.Default() is None:
        #    raise InvalidOperationException('Default blockchain None')

        cbh = Blockchain.Default().CurrentBlockHash
        corrected_hash = bytearray.fromhex(cbh.decode('utf8'))
        corrected_hash.reverse()
        uint256_cur_hash = UInt256(data=corrected_hash)

        if self.PrevHash != uint256_cur_hash:
            raise InvalidOperationException(
                "PrevHash != CurrentBlockHash\r\n{} != {}".format(self.PrevHash, uint256_cur_hash))

        validators = Blockchain.Default().GetValidators(others=[])
        if len(validators) < self.ValidatorIndex:
            raise InvalidOperationException('ValidatorIndex out of range')

        public_key = validators[self.ValidatorIndex]
        return [VerificationContract.CreateSignatureContract(public_key).ScriptHash]

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader(neo.IO.BinaryReader):
        """
        self.DeserializeUnsigned(reader)
        if reader.ReadByte() != 1:
            raise Exception()
        w = Witness()
        w.Deserialize(reader)
        self.Script = w

    def DeserializeUnsigned(self, reader):
        """
        Deserialize unsigned data only.

        Args:
            reader(neo.IO.BinaryReader):
        """
        self.Version = reader.ReadUInt32()
        self.PrevHash = reader.ReadUInt256()
        self.BlockIndex = reader.ReadUInt32()
        self.ValidatorIndex = reader.ReadUInt16()
        self.Timestamp = reader.ReadUInt32()
        self.Data = reader.ReadVarBytes()

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            reader(neo.IO.BinaryWriter):
        """
        self.SerializeUnsigned(writer)
        writer.WriteByte(1)
        self.Script.Serialize(writer)

    def SerializeUnsigned(self, writer):
        """
        Serialize unsigned data only.

        Args:
            reader(neo.IO.BinaryWriter):
        """
        writer.WriteUInt32(self.Version)
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt32(self.BlockIndex)
        writer.WriteUInt16(self.ValidatorIndex)
        writer.WriteUInt32(self.Timestamp)
        writer.WriteVarBytes(self.Data)

    def Verify(self):
        """
        Verify the Script of the payload.

        Returns:
            bool: True if valid, False otherwise.
        """
        # if Blockchain.Default() is None: # see comment at self.GetScriptHashesForVerifying
        #     return False
        cbh = Blockchain.Default().CurrentBlockHash
        corrected_hash = bytearray.fromhex(cbh.decode('utf8'))
        corrected_hash.reverse()
        uint256_cur_hash = UInt256(data=corrected_hash)

        if self.PrevHash != uint256_cur_hash:
            return False
        if self.BlockIndex != Blockchain.Default().Height + 1:
            return False

        return Helper.VerifyScripts(self)

    def GetHashData(self):
        """
        Get the hash data of the payload. Same result as GetMessage().

        Returns:
            bytes: a hexstring encapsulated in a bytes() object.
        """
        return Helper.GetHashData(self)

    @property
    def Scripts(self):
        """
        Get the Script object.

        Returns:
            Witness: the Script.
        """
        return [self.Script]

    @Scripts.setter
    def Scripts(self, value):
        """
        Set the Script item to `value`.

        Args:
            value(list): holding exactly 1 Witnes() object.
        """
        if len(value) != 1:
            raise ValueError('expect value to be a list of length 1')

        if not isinstance(value[0], Witness):
            raise ValueError('List item is not a Witness object')

        self.Script = value[0]
