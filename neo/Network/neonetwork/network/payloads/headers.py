from neo.Network.neonetwork.network.payloads.base import BasePayload
from typing import TYPE_CHECKING, Optional, Union, List
from neo.Network.neonetwork.core.header import Header
from neo.Network.neonetwork.core.io.binary_writer import BinaryWriter
from neo.Network.neonetwork.core.io.binary_reader import BinaryReader

if TYPE_CHECKING:
    from neo.Network.neonetwork.core.io import BinaryReader


class HeadersPayload(BasePayload):
    def __init__(self, headers: Optional[List[Header]] = None):
        self.headers = headers if headers else []

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        len_headers = len(self.headers)
        if len_headers == 0:
            writer.write_uint8(0)
        else:
            writer.write_var_int(len_headers)
            for header in self.headers:
                header.serialize(writer)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object

        Raises:
            DeserializationError: if deserialization fails
        """
        arr_length = reader.read_var_int()
        for i in range(arr_length):
            h = Header(None, None, None, None, None, None, None)
            h.deserialize(reader)
            self.headers.append(h)

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]) -> 'HeadersPayload':
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        headers_payload = cls()
        headers_payload.deserialize(br)
        return headers_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = writer._stream.getbuffer()
        return bytearray(data)
