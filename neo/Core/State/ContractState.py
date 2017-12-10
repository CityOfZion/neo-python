from .StateBase import StateBase
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Core.FunctionCode import FunctionCode

from enum import IntEnum


class ContractPropertyState(IntEnum):
    NoProperty = 0
    HasStorage = 1 << 0
    HasDynamicInvoke = 1 << 1


class ContractState(StateBase):

    Code = None
    ContractProperties = None
    Name = None
    CodeVersion = None
    Author = None
    Email = None
    Description = None

    @property
    def HasStorage(self):
        return self.ContractProperties & ContractPropertyState.HasStorage > 0

    @property
    def HasDynamicInvoke(self):
        return self.ContractProperties & ContractPropertyState.HasDynamicInvoke > 0

    def __init__(self, code=None, contract_properties=0, name=None, version=None, author=None, email=None, description=None):
        self.Code = code
        self.ContractProperties = contract_properties
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

        self.ContractProperties = reader.ReadUInt8()
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
        writer.WriteUInt8(self.ContractProperties)
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

        print("self contract properties: %s " % self.ContractProperties)

        return {

            'version': self.StateVersion,
            'code': codejson,
            'name': name,
            'code_version': self.CodeVersion.decode('utf-8'),
            'author': self.Author.decode('utf-8'),
            'email': self.Email.decode('utf-8'),
            'description': self.Description.decode('utf-8'),
            'properties': {
                'storage': self.HasStorage,
                'dynamic_invoke': self.HasDynamicInvoke
            }
        }
