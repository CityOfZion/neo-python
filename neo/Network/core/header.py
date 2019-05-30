from neo.Network.core.blockbase import BlockBase
from neo.Network.core.exceptions import DeserializationError
from neo.Network.core.uint256 import UInt256
from typing import Union
from neo.Network.core.io.binary_reader import BinaryReader
from neo.Network.core.io.binary_writer import BinaryWriter


class Header(BlockBase):
    def __init__(self, prev_hash, merkle_root, timestamp, index, consensus_data, next_consensus, witness):
        version = 0
        temp_merkeroot = UInt256.zero()
        super(Header, self).__init__(version, prev_hash, temp_merkeroot, timestamp, index, consensus_data, next_consensus, witness)

        self.prev_hash = prev_hash
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.index = index
        self.consensus_data = consensus_data
        self.next_consensus = next_consensus
        self.witness = bytearray()  # witness

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        super(Header, self).serialize(writer)
        writer.write_uint8(0)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object

        Raises:
             DeserializationError: if insufficient or incorrect data
        """
        super(Header, self).deserialize(reader)
        try:
            val = reader.read_byte()
            if int(val.hex()) != 0:
                raise DeserializationError(f"expected 0 got {val}")
        except ValueError as ve:
            raise DeserializationError(str(ve))

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]) -> 'Header':
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        header = cls(None, None, None, None, None, None, None)
        try:
            header.deserialize(br)
        except DeserializationError:
            return None
        br.cleanup()
        return header

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
