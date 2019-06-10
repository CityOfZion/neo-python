import hashlib
from neo.Network.core.exceptions import DeserializationError
from neo.Network.core.mixin.serializable import SerializableMixin
from neo.Network.core.uint256 import UInt256
from neo.Network.core.uint160 import UInt160
from neo.Network.core.io.binary_reader import BinaryReader
from neo.Network.core.io.binary_writer import BinaryWriter


class BlockBase(SerializableMixin):

    def __init__(self, version: int, prev_hash: UInt256, merkle_root: UInt256, timestamp: int, index: int, consensus_data, next_consensus: UInt160, witness):
        self.version = version
        self.prev_hash = prev_hash
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.index = index
        self.consensus_data = consensus_data
        self.next_consensus = next_consensus
        self.witness = bytearray()  # witness

    @property
    def hash(self):
        writer = BinaryWriter(stream=bytearray())
        self.serialize_unsigned(writer)
        hash_data = writer._stream.getvalue()
        hash = hashlib.sha256(hashlib.sha256(hash_data).digest()).digest()
        writer.cleanup()
        return UInt256(data=hash)

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        self.serialize_unsigned(writer)

        writer.write_uint8(1)
        # TODO: Normally we should write a Witness object
        #       we did not implement this at this moment because we don't need this data.
        # writer.write_var_bytes(self.witness)
        # so instead we just write 0 length indicators for the 2 members of script
        writer.write_var_int(0)  # invocation script length
        writer.write_var_int(0)  # verification script length

    def serialize_unsigned(self, writer: 'BinaryWriter') -> None:
        """ Serialize unsigned object data only. """
        writer.write_uint32(self.version)
        writer.write_uint256(self.prev_hash)
        writer.write_uint256(self.merkle_root)
        writer.write_uint32(self.timestamp)
        writer.write_uint32(self.index)
        writer.write_uint64(self.consensus_data)
        writer.write_uint160(self.next_consensus)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self.version = reader.read_uint32()
        self.prev_hash = reader.read_uint256()
        self.merkle_root = reader.read_uint256()
        self.timestamp = reader.read_uint32()
        self.index = reader.read_uint32()
        self.consensus_data = reader.read_uint64()
        self.next_consensus = reader.read_uint160()

        val = reader.read_byte()
        if int(val.hex()) != 1:
            raise DeserializationError(f"expected 1 got {val}")

        # TODO: self.witness = reader.read(Witness())
        #       witness consists of InvocationScript + VerificationScript
        #       instead of a full implementation we just have a bytearray as we don't need the data
        raw_witness = reader.read_var_bytes()  # invocation script
        raw_witness += reader.read_var_bytes()  # verification script

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
