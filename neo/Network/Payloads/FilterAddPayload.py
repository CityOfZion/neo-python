
from neo.IO.Mixins import SerializableMixin
import sys


class FilterAddPayload(SerializableMixin):

    Data = None

    def __init__(self, data=None):
        self.Data = data

    def Size(self):
        return sys.getsizeof(self.Data)

    def Deserialize(self, reader):
        self.Data = reader.ReadVarBytes(520)

    def Serialize(self, writer):
        writer.WriteVarBytes(self.Data)
