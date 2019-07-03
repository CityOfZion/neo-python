from .StateBase import StateBase
from neo.Core.IO.BinaryReader import BinaryReader
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager
from neo.Core.Cryptography.ECCurve import EllipticCurve, ECDSA
from neo.Core.Size import Size as s
from neo.Core.Size import GetVarSize
from neo.Core.Fixed8 import Fixed8


class ValidatorState(StateBase):
    def __init__(self, pub_key=None):
        """
        Create an instance.

        Args:
            pub_key (EllipticCurve.ECPoint):

        Raises:
            Exception: if `pub_key` is not a valid ECPoint.
        """
        if pub_key is not None and type(pub_key) is not EllipticCurve.ECPoint:
            raise Exception("Pubkey must be ECPoint Instance")

        self.PublicKey = pub_key
        self.Registered = False
        self.Votes = Fixed8.Zero()

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(ValidatorState, self).Size() + self.PublicKey.Size() + s.uint8 + self.Votes.Size()

    def Deserialize(self, reader: BinaryReader):
        """
        Deserialize full object.

        Args:
            reader (neo.Core.IO.BinaryReader):
        """
        super(ValidatorState, self).Deserialize(reader)
        self.PublicKey = ECDSA.Deserialize_Secp256r1(reader)
        self.Registered = reader.ReadBool()
        self.Votes = reader.ReadFixed8()

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
        v = ValidatorState()
        v.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return v

    def Serialize(self, writer: BinaryWriter):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(ValidatorState, self).Serialize(writer)
        self.PublicKey.Serialize(writer)
        writer.WriteBool(self.Registered)
        writer.WriteFixed8(self.Votes)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        return {
            'pubkey': self.PublicKey.ToString()
        }

    def Clone(self):
        vs = ValidatorState(self.PublicKey)
        vs.Registered = self.Registered
        vs.Votes = self.Votes
        return vs
