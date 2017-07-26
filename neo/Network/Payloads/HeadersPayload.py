
from neo.IO.Mixins import SerializableMixin
import sys

class HeadersPayload(SerializableMixin):

    Headers = []

    def __init__(self, headers):
        self.Headers = headers if headers else []


    def Size(self):
        return sys.getsizeof(self.Headers)


    def Deserialize(self, reader):
        self.Headers = reader.ReadSerializableArray(2000)

    def Serialize(self, writer):
        writer.Write(self.Headers)
