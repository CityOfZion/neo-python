
from neo.IO.Mixins import SerializableMixin
import binascii
from neo.Cryptography.Helper import hash_to_wallet_address

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


    def ToJson(self):
        return {
            'hash': hash_to_wallet_address(self.Script),
            'script': bytearray(self.Script).hex(),
            'parameters': bytearray(self.ParameterList).hex(),
            'returntype': self.ReturnType if type(self.ReturnType) is int else self.ReturnType.decode('utf-8')
        }