
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.Cryptography.ECCurve import EllipticCurve, ECDSA


class ValidatorState(StateBase):

    PublicKey = None

    def __init__(self, pub_key=None):

        if pub_key is not None and type(pub_key) is not EllipticCurve.ECPoint:
            raise Exception("Pubkey must be ECPoint Instance")

        self.PublicKey = pub_key

    def Size(self):
        return super(ValidatorState, self).Size()

    def Deserialize(self, reader):
        super(ValidatorState, self).Deserialize(reader)
        self.PublicKey = ECDSA.Deserialize_Secp256r1(reader)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        v = ValidatorState()
        v.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return v

    def Serialize(self, writer):
        super(ValidatorState, self).Serialize(writer)
        self.PublicKey.Serialize(writer)

    def ToJson(self):
        return {
            'pubkey': self.PublicKey.ToString()
        }
