from neo.Network.payloads.base import BasePayload
from neo.Network.core.uint256 import UInt256
from typing import TYPE_CHECKING, Union
from neo.Network.core.io.binary_writer import BinaryWriter

if TYPE_CHECKING:
    from neo.Network.core import BinaryReader


class GetBlocksPayload(BasePayload):
    def __init__(self, start: UInt256, stop: UInt256 = None):
        self.hash_start = [start]
        self.hash_stop = stop if stop else UInt256.zero()

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        length = len(self.hash_start)
        writer.write_var_int(length)
        for hash in self.hash_start:
            writer.write_uint256(hash)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        length = reader.read_var_int()
        self.hash_start = list(map(reader.read_uint256(), range(length)))
        self.hash_stop = reader.read_uint256()

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]):
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        block_payload = cls()
        block_payload.deserialize(br)
        br.cleanup()
        return block_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
