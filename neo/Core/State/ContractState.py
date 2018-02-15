from .StateBase import StateBase
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Core.FunctionCode import FunctionCode
from enum import IntEnum
import binascii


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

    _is_nep5 = None
    _nep_token = None

    @property
    def HasStorage(self):
        """
        Flag indicating if the contract has storage.

        Returns:
            bool: True if available. False otherwise.
        """
        return self.ContractProperties & ContractPropertyState.HasStorage > 0

    @property
    def HasDynamicInvoke(self):
        """
        Flag indicating if the contract supports dynamic invocation.

        Returns:
            bool: True if supported. False otherwise.
        """
        return self.ContractProperties & ContractPropertyState.HasDynamicInvoke > 0

    @property
    def IsNEP5Contract(self):
        """
        Property to indicate whether this is an NEP5 Contract
        Returns:
            bool
        """
        if self._is_nep5 is None:
            self.DetermineIsNEP5()
        return self._is_nep5

    def __init__(self, code=None, contract_properties=0, name=None, version=None, author=None, email=None,
                 description=None):
        """
        Create an instance.

        Args:
            code (neo.Core.FunctionCode):
            contract_properties (neo.SmartContract.ContractParameterType): contract type.
            name (bytes):
            version (bytes):
            author (bytes):
            email (bytes):
            description (bytes):
        """
        self.Code = code
        self.ContractProperties = contract_properties
        self.Name = name
        self.CodeVersion = version
        self.Author = author
        self.Email = email
        self.Description = description

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(ContractState, self).Size()

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
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
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            ContractState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        c = ContractState()
        c.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return c

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(ContractState, self).Serialize(writer)

        self.Code.Serialize(writer)
        writer.WriteUInt8(self.ContractProperties)
        writer.WriteVarString(self.Name)
        writer.WriteVarString(self.CodeVersion)
        writer.WriteVarString(self.Author)
        writer.WriteVarString(self.Email)
        writer.WriteVarString(self.Description)

    def DetermineIsNEP5(self):
        """
        Determines if this Smart contract is an NEP5 Token or not.
        Returns:
            bool
        """
        from neo.Wallets.NEP5Token import NEP5Token

        self._is_nep5 = False
        token = NEP5Token(binascii.hexlify(self.Code.Script))
        if token.Query():
            self._nep_token = token
            self._is_nep5 = True
        return self._is_nep5

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        codejson = self.Code.ToJson()

        name = 'Contract'

        try:
            name = self.Name.decode('utf-8')
        except Exception as e:
            pass

        jsn = {

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

        if self._nep_token:
            jsn['token'] = self._nep_token.ToJson()

        return jsn
