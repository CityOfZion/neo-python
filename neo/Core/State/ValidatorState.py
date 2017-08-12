
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream

class ValidatorState(StateBase):


    PublicKey = None

    def __init__(self, pub_key=None):
        self.PublicKey = pub_key

    def Size(self):
        return super(ValidatorState, self).Size()

    def Deserialize(self, reader):
        super(ValidatorState, self).Deserialize(reader)
        self.PublicKey = reader.ReadBytes(33)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        v = ValidatorState()
        v.Deserialize(reader)

        m.Cleanup()
        m = None

        return v

    def Serialize(self, writer):
        super(ValidatorState, self).Serialize(writer)
        writer.WriteBytes(self.PublicKey)
