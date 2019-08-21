from neo.Network.payloads.base import BasePayload
from neo.Network.core.io.binary_writer import BinaryWriter
from neo.Network.core.io.binary_reader import BinaryReader
from typing import List, Union
from neo.Network.payloads.networkaddress import NetworkAddressWithTime


class AddrPayload(BasePayload):
    def __init__(self, addresses: List[NetworkAddressWithTime] = None):
        self.addresses = addresses if addresses else []

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_var_int(len(self.addresses))
        for address in self.addresses:
            address.serialize(writer)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        addr_list_len = reader.read_var_int()
        for i in range(0, addr_list_len):
            nawt = NetworkAddressWithTime()
            nawt.deserialize(reader)
            self.addresses.append(nawt)

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]):
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        addr_payload = cls()
        addr_payload.deserialize(br)
        br.cleanup()
        return addr_payload

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
