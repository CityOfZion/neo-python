from neo.IO.Mixins import SerializableMixin
import binascii

class UIntBase(SerializableMixin):


    _data = bytearray()



    def __init__(self, num_bytes, data=None):
        super(UIntBase, self).__init__()

        if data is None:
            self._data = bytearray(num_bytes)

        elif len(data) != num_bytes:
            raise Exception("Invalid UInt")

        if type(data) is bytes:
            self._data = bytearray(data)
        elif type(data) is bytearray:
            self._data = data
        else:
            raise Exception("Invalid format")

    @property
    def Data(self):
        return self._data

    @property
    def Size(self):
        return len(self._data)

    def GetHashCode(self):

        return int.from_bytes(self._data[:4], 'little')


    def Serialize(self, writer):
        writer.WriteBytes(self._data)

    def Deserialize(self, reader):
        self._data = reader.ReadBytes(self.Size)

    def ToArray(self):
        return self._data


    def ToString(self):
        db = bytearray(self._data)
        db.reverse()
        return db.hex()


    def ToBytes(self):
        return bytes(self.ToString(), encoding='utf-8')


    def __eq__(self, other):
        if other is None:
            return False
        if( type(self) != type(self)):
            return False

        if other is self:
            return True

        if self._data == other._data:
            return True


    def __hash__(self):
        return int.from_bytes(self._data, 'little')