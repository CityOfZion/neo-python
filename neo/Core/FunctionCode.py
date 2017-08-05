
from neo.IO.Mixins import SerializableMixin

class FunctionCode(SerializableMixin):


    Script = bytearray()

    ParameterList = bytearray()

    ReturnType = None


    _scriptHash = None


    def Deserialize(self, reader):

        self.Script = reader.ReadVarBytes()

        self.ParameterList = reader.ReadVarBytes()
        self.ReturnType = reader.ReadByte()


    def Serialize(self, writer):
        writer.WriteVarBytes(self.Script)

        writer.WriteVarBytes( self.ParameterList)
        writer.WriteByte(self.ReturnType)

