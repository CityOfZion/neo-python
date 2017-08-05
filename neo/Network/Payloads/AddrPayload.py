
from neo.IO.Mixins import SerializableMixin
import sys

class AddrPayload(SerializableMixin):

    NetworkAddressesWithTime = []

    def __init__(self, addresses=None):
        self.NetworkAddressesWithTime = addresses if addresses else []

    def Size(self):
        return sys.getsizeof(self.NetworkAddressesWithTime)


    def Deserialize(self, reader):
        self.NetworkAddressesWithTime = reader.ReadSerializableArray()


    def Serialize(self, writer):
        for address in self.NetworkAddressesWithTime:
            address.Serialize(writer)

