from neo.Network.payloads.base import BasePayload
from enum import Enum
from typing import Union, List
from neo.Network.core.io.binary_writer import BinaryWriter
from neo.Network.core.io.binary_reader import BinaryReader
from neo.Network.core.uint256 import UInt256


class InventoryType(Enum):
    tx = 0x01
    block = 0x02
    consensus = 0xe0


class InventoryPayload(BasePayload):

    def __init__(self, type: InventoryType = None, hashes: List[UInt256] = None):
        self.type = type
        self.hashes = hashes if hashes else []

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_uint8(self.type.value)
        writer.write_var_int(len(self.hashes))
        for h in self.hashes:  # type: UInt256
            writer.write_bytes(h.to_array())

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self.type = InventoryType(reader.read_uint8())
        self.hashes = []
        hash_list_count = reader.read_var_int()

        try:
            for i in range(0, hash_list_count):
                self.hashes.append(UInt256(data=reader.read_bytes(32)))
        except ValueError:
            raise ValueError("Invalid hashes data")

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]):
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        inv_payload = cls()
        try:
            inv_payload.deserialize(br)
        except ValueError:
            return None
        finally:
            br.cleanup()
        return inv_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
