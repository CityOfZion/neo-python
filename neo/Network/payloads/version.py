import datetime
import random
from typing import Union
from neo.Network.core.size import Size as s
from neo.Network.core.size import GetVarSize
from neo.Network.payloads.base import BasePayload
from neo.Network.payloads.networkaddress import NetworkAddressWithTime
from neo.Network.core.io.binary_writer import BinaryWriter
from neo.Network.core.io.binary_reader import BinaryReader


class VersionPayload(BasePayload):

    def __init__(self, port: int = None, nonce: int = None, userAgent: str = None) -> None:
        """
        Create an instance.

        Args:
            port:
            nonce:
            userAgent: client user agent string.
        """
        # if port and nonce and userAgent:
        self.port = port
        self.version = 0
        self.services = NetworkAddressWithTime.NODE_NETWORK
        self.timestamp = int(datetime.datetime.utcnow().timestamp())
        self.nonce = nonce if nonce else random.randint(0, 10000)
        self.user_agent = userAgent if userAgent else ""
        self.start_height = 0  # TODO: update once blockchain class is available
        self.relay = True

    def __len__(self):
        return self.size()

    def size(self) -> int:
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return s.uint32 + s.uint64 + s.uint32 + s.uint16 + s.uint32 + GetVarSize(self.user_agent) + s.uint32 + s.uint8

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_uint32(self.version)
        writer.write_uint64(self.services)
        writer.write_uint32(self.timestamp)
        writer.write_uint16(self.port)
        writer.write_uint32(self.nonce)
        writer.write_var_string(self.user_agent)
        writer.write_uint32(self.start_height)
        writer.write_bool(self.relay)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self.version = reader.read_uint32()
        self.services = reader.read_uint64()
        self.timestamp = reader.read_uint32()
        self.port = reader.read_uint16()
        self.nonce = reader.read_uint32()
        self.user_agent = reader.read_var_string()
        self.start_height = reader.read_uint32()
        self.relay = reader.read_bool()

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]):
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        version_payload = cls()
        version_payload.deserialize(br)
        br.cleanup()
        return version_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
