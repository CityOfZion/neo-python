import hashlib
from typing import Union
from typing import TYPE_CHECKING, Optional
from neo.Network.payloads.base import BasePayload
from neo.Network.core.mixin.serializable import SerializableMixin
from neo.Network.core.size import Size as s
from neo.Network.core.io.binary_writer import BinaryWriter

bytes_or_payload = Union[bytes, BasePayload]

if TYPE_CHECKING:
    from neo.Network.core import BinaryReader


class ChecksumException(Exception):
    pass


class Message(SerializableMixin):
    _payload_max_size = int.from_bytes(bytes.fromhex('02000000'), 'big')
    _magic = None

    def __init__(self, magic: Optional[int] = None, command: Optional[str] = None, payload: Optional[bytes_or_payload] = None) -> None:
        """
        Create an instance.

        Args:
            command: max 12 bytes, utf-8 encoded payload command
            payload: raw bytes of the payload.
        """
        self.command = command
        if magic:
            self.magic = magic
        else:
            # otherwise set to class variable.
            self.magic = self._magic

        self.payload_length = 0
        if payload is None:
            self.payload = bytearray()
        else:
            if isinstance(payload, BasePayload):
                self.payload = payload.to_array()
            else:
                self.payload = payload
            self.payload_length = len(self.payload)

        self.checksum = None

    def __len__(self) -> int:
        return self.size()

    def size(self) -> int:
        """ Get the total size in bytes of the object. """
        return s.uint32 + 12 + s.uint32 + s.uint32 + len(self.payload)

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_uint32(self.magic)
        writer.write_fixed_string(self.command, 12)
        writer.write_uint32(len(self.payload))
        writer.write_uint32(self.get_checksum())
        writer.write_bytes(self.payload)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize full object. """
        self.magic = reader.read_uint32()
        self.command = reader.read_fixed_string(12)
        self.payload_length = reader.read_uint32()

        if self.payload_length > self._payload_max_size:
            raise ValueError("Specified payload length exceeds maximum payload length")

        self.checksum = reader.read_uint32()
        self.payload = reader.read_bytes(self.payload_length)

        checksum = self.get_checksum()

        if checksum != self.checksum:
            raise ChecksumException("checksum mismatch")

    def get_checksum(self, value: Optional[Union[bytes, bytearray]] = None) -> int:
        """
        Get the double SHA256 hash of the value.

        Args:
            value (raw bytes): a payload

        Returns:
            int: checksum
        """
        if not value:
            value = self.payload

        uint32 = hashlib.sha256(hashlib.sha256(value).digest()).digest()
        x = uint32[:4]
        return int.from_bytes(x, 'little')

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
