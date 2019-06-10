from typing import TYPE_CHECKING
from datetime import datetime
from neo.Network.core.size import Size as s
from neo.Network.payloads.base import BasePayload

if TYPE_CHECKING:
    from neo.Network.core import BinaryReader
    from neo.Network.core.io.binary_writer import BinaryWriter


class NetworkAddressWithTime(BasePayload):
    NODE_NETWORK = 1

    def __init__(self, address: str = None, port: int = None, services: int = 0, timestamp: int = None) -> None:
        """ Create an instance. """
        if timestamp is None:
            self.timestamp = int(datetime.utcnow().timestamp())
        else:
            self.timestamp = timestamp

        self.address = address
        self.port = port
        self.services = services

    @property
    def size(self) -> int:
        """ Get the total size in bytes of the object. """
        return s.uint32 + s.uint64 + 16 + s.uint16

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_uint32(self.timestamp)
        writer.write_uint64(self.services)
        # turn ip address into bytes
        octets = bytearray(map(lambda oct: int(oct), self.address.split('.')))
        # pad to fixed length 16
        octets += bytearray(12)
        # and finally write to stream
        writer.write_bytes(octets)

        writer.write_uint16(self.port, endian='>')

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self.timestamp = reader.read_uint32()
        self.services = reader.read_uint64()
        full_address_bytes = bytearray(reader.read_fixed_string(16))
        ip_bytes = full_address_bytes[-4:]
        self.address = '.'.join(map(lambda b: str(b), ip_bytes))
        self.port = reader.read_uint16(endian='>')

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data

    def __str__(self) -> str:
        """
        Get the string representation of the network address.

        Returns:
            str: address:port
        """
        return f"{self.address}:{self.port}"
