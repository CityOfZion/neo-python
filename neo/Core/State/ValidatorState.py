from .StateBase import StateBase
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neocore.Cryptography.ECCurve import EllipticCurve, ECDSA


class ValidatorState(StateBase):
    PublicKey = None

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

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(ValidatorState, self).Size()

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        super(ValidatorState, self).Deserialize(reader)
        self.PublicKey = ECDSA.Deserialize_Secp256r1(reader)

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

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(ValidatorState, self).Serialize(writer)
        self.PublicKey.Serialize(writer)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        return {
            'pubkey': self.PublicKey.ToString()
        }
