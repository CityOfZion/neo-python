from typing import Union
from neo.Network.core.size import Size as s
from neo.Network.payloads.base import BasePayload
from neo.Network.core.io.binary_writer import BinaryWriter
from neo.Network.core.io.binary_reader import BinaryReader
from datetime import datetime
from random import randint


class PingPayload(BasePayload):
    def __init__(self, height: int = 0) -> None:
        self.current_height = height
        self.timestamp = int(datetime.utcnow().timestamp())
        self.nonce = randint(100, 10000)

    def __len__(self):
        return self.size()

    def size(self) -> int:
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return s.uint32 + s.uint32 + s.uint32

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_uint32(self.current_height)
        writer.write_uint32(self.timestamp)
        writer.write_uint32(self.nonce)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self.current_height = reader.read_uint32()
        self.timestamp = reader.read_uint32()
        self.nonce = reader.read_uint32()

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]) -> 'PingPayload':
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        ping_payload = cls()
        ping_payload.deserialize(br)
        br.cleanup()
        return ping_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
