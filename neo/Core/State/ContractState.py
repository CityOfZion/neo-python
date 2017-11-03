
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.Core.FunctionCode import FunctionCode


class ContractState(StateBase):

    Code = None
    HasStorage = False
    Name = None
    CodeVersion = None
    Author = None
    Email = None
    Description = None

    def __init__(self, code=None, has_storage=False, name=None, version=None, author=None, email=None, description=None):
        self.Code = code
        self.HasStorage = has_storage
        self.Name = name
        self.CodeVersion = version
        self.Author = author
        self.Email = email
        self.Description = description

    def Size(self):
        return super(ContractState, self).Size()

    def Deserialize(self, reader):
        super(ContractState, self).Deserialize(reader)

        code = FunctionCode()
        code.Deserialize(reader)
        self.Code = code

        self.HasStorage = reader.ReadBool()
        self.Name = reader.ReadVarString(max=252)
        self.CodeVersion = reader.ReadVarString(max=252)
        self.Author = reader.ReadVarString(max=252)
        self.Email = reader.ReadVarString(max=252)
        self.Description = reader.ReadVarString(max=65536)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        c = ContractState()
        c.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return c

    def Serialize(self, writer):
        super(ContractState, self).Serialize(writer)

        self.Code.Serialize(writer)
        writer.WriteBool(self.HasStorage)
        writer.WriteVarString(self.Name)
        writer.WriteVarString(self.CodeVersion)
        writer.WriteVarString(self.Author)
        writer.WriteVarString(self.Email)
        writer.WriteVarString(self.Description)

    def ToJson(self):

        codejson = self.Code.ToJson()

        name = 'Contract'

        try:
            name = self.Name.decode('utf-8')
        except Exception as e:
            pass

        return {

            'version': self.StateVersion,
            'code': codejson,
            'storage': self.HasStorage,
            'name': name,
            'code_version': self.CodeVersion.decode('utf-8'),
            'author': self.Author.decode('utf-8'),
            'email': self.Email.decode('utf-8'),
            'description': self.Description.decode('utf-8')
        }
