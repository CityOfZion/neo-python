from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Core.Mixins import SerializableMixin
from neo.IO.MemoryStream import StreamManager
from neocore.Fixed8 import Fixed8

from enum import Enum


class StateType(Enum):
    Account = 0x40
    Validator = 0x48


class StateDescriptor(SerializableMixin):

    Type = None
    Key = None
    Field = None
    Value = None

    @property
    def SystemFee(self):
        if self.Type == StateType.Account:
            return Fixed8.Zero()
        elif self.Type == StateType.Validator:
            return self.GetSystemFee_Validator()

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(StateDescriptor, self).Size()

    def Deserialize(self, reader: BinaryReader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """

        self.Type = StateType(reader.ReadByte())

        self.Key = reader.ReadVarBytes(max=100)
        self.Field = reader.ReadVarString(max=32).decode('utf-8')
        self.Value = reader.ReadVarBytes(max=65535)

        if self.Type == StateType.Account:
            self.CheckAccountState()
        elif self.Type == StateType.Validator:
            self.CheckValidatorState()

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            ValidatorState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        v = StateDescriptor()
        v.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return v

    def Serialize(self, writer: BinaryWriter):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        byt = None
        if self.Type == StateType.Account:
            byt = b'\x40'
        elif self.Type == StateType.Validator:
            byt = b'\x48'
        writer.WriteByte(byt)
        writer.WriteVarBytes(self.Key)
        writer.WriteVarString(self.Field)
        writer.WriteVarBytes(self.Value)

    def GetSystemFee_Validator(self):

        if self.Field == "Registered":
            for character in self.Value:
                if character != '0':
                    return Fixed8.FromDecimal(1000)
            return Fixed8.Zero()

        raise Exception("Invalid operation")

    def CheckAccountState(self):
        if len(self.Key) != 20:
            raise Exception("Invalid Key format")
        if self.Field != "Votes":
            raise Exception("Invalid Field")

    def CheckValidatorState(self):
        if len(self.Key) != 33:
            raise Exception("Invalid Validator State Key Format")
        if self.Field != "Registered":
            raise Exception("Invalid Field for validator")

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """

        type = ''
        if self.Type == StateType.Validator:
            type = 'Validator'
        elif self.Type == StateType.Account:
            type = 'Account'

        return {
            'type': type,
            'key': self.Key.hex(),
            'field': self.Field,
            'value': self.Value.hex()
        }

    def Verify(self):

        if self.Type == StateType.Account:
            return self.VerifyAccountState()
        elif self.Type == StateType.Validator:
            return self.VerifyValidatorState()
        raise Exception("Invalid State Descriptor")

    def VerifyAccountState(self):
        # @TODO
        # Implement VerifyAccount State
        raise NotImplementedError()

    def VerifyValidatorState(self):
        if self.Field == 'Registered':
            return True
        return False
