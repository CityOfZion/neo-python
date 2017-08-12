
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
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
        self.Name = reader.ReadVarString()
        self.CodeVersion = reader.ReadVarString()
        self.Author = reader.ReadVarString()
        self.Email = reader.ReadVarString()
        self.Description = reader.ReadVarString()

    @staticmethod
    def DeserializeFromDB(buffer):
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        c = ContractState()
        c.Deserialize(reader)

        m.Cleanup()
        m = None

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
