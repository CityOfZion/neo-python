
from neo.IO.Mixins import SerializableMixin
import sys


class HeadersPayload(SerializableMixin):

    Headers = []

    def __init__(self, headers=None):
        self.Headers = headers if headers else []

    def Size(self):
        return sys.getsizeof(self.Headers)

    def Deserialize(self, reader):
        self.Headers = reader.ReadSerializableArray('neo.Core.Header.Header')

    def Serialize(self, writer):
        writer.Write(self.Headers)
