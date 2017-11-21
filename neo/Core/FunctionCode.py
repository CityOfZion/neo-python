
from neo.IO.Mixins import SerializableMixin
import binascii
from neo.Cryptography.Helper import hash_to_wallet_address
from neo.Cryptography.Helper import hash_to_wallet_address
from neo.Cryptography.Crypto import Crypto


class FunctionCode(SerializableMixin):

    Script = bytearray()

    ParameterList = bytearray()

    ReturnType = None

    _scriptHash = None

    NeedsStorage = False

    def __init__(self, script=None, param_list=None, return_type=None, needs_storage=False):
        self.Script = script
        if param_list is None:
            self.ParameterList = []
        else:
            self.ParameterList = param_list

        self.ReturnType = return_type

        self.NeedsStorage = needs_storage

    def ScriptHash(self):
        if self._scriptHash is None:
            self._scriptHash = Crypto.ToScriptHash(self.Script, unhex=False)

        return self._scriptHash

    def Deserialize(self, reader):

        self.Script = reader.ReadVarBytes()

        self.ParameterList = reader.ReadVarBytes()
        self.ReturnType = reader.ReadByte()

    def Serialize(self, writer):
        writer.WriteVarBytes(self.Script)

        writer.WriteVarBytes(self.ParameterList)
        writer.WriteByte(self.ReturnType)

    def ToJson(self):
        return {
            'hash': self.ScriptHash().ToString(),
            'script': self.Script.hex(),
            'parameters': self.ParameterList.hex(),
            'returntype': self.ReturnType if type(self.ReturnType) is int else self.ReturnType.hex()
        }
