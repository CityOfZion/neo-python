
from neo.IO.Mixins import SerializableMixin
import sys


class AddrPayload(SerializableMixin):

    NetworkAddressesWithTime = []

    def __init__(self, addresses=None):
        self.NetworkAddressesWithTime = addresses if addresses else []

    def Size(self):
        return sys.getsizeof(self.NetworkAddressesWithTime)

    def Deserialize(self, reader):
        self.NetworkAddressesWithTime = reader.ReadSerializableArray('neo.Network.Payloads.NetworkAddressWithTime.NetworkAddressWithTime')

    def Serialize(self, writer):
        writer.WriteVarInt(len(self.NetworkAddressesWithTime))
        for address in self.NetworkAddressesWithTime:
            address.Serialize(writer)
