from neo.IO.Mixins import SerializableMixin
import binascii

class UIntBase(SerializableMixin):


    Data = bytearray()

    __hash = None

    def __init__(self, num_bytes, data=None):
        super(UIntBase, self).__init__()

        if data is None:
            self.Data = bytearray(num_bytes)

        else:
            if len(data) != num_bytes:
                raise Exception("Invalid UInt")

            if type(data) is bytes:
                self.Data = bytearray(data)
            elif type(data) is bytearray:
                self.Data = data
            else:
                raise Exception("Invalid format")

        self.__hash = self.GetHashCode()
    @property
    def Size(self):
        return len(self.Data)

    def GetHashCode(self):

        return int.from_bytes(self.Data[:4], 'little')


    def Serialize(self, writer):
        writer.WriteBytes(self.Data)

    def Deserialize(self, reader):
        self.Data = reader.ReadBytes(self.Size)
        self.__hash = self.GetHashCode()

    def ToArray(self):
        return self.Data


    def ToString(self):
        db = bytearray(self.Data)
        db.reverse()
        return db.hex()

    def ToString2(self):
        return self.Data.hex()

    def ToBytes(self):
        return bytes(self.ToString(), encoding='utf-8')


    def __eq__(self, other):
        if other is None:
            return False
        if( type(self) != type(self)):
            return False

        if other is self:
            return True

        if self.Data == other.Data:
            return True


    def __hash__(self):
        return self.__hash