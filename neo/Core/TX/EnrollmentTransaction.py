from neo.Core.TX.Transaction import Transaction, TransactionType
import sys
from neocore.Cryptography.ECCurve import ECDSA
from neo.Settings import settings
from neocore.Fixed8 import Fixed8


class EnrollmentTransaction(Transaction):
    PublicKey = None
    _script_hash = None

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(EnrollmentTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.EnrollmentTransaction

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(EnrollmentTransaction, self).Size() + sys.getsizeof(int)

    def SystemFee(self):
        """
        Get the enrollment fee.

        Returns:
            Fixed8:
        """
        return Fixed8(int(settings.ENROLLMENT_TX_FEE))

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):

        Raises:
            Exception: If the version read is incorrect.
        """
        if self.Version is not 0:
            raise Exception('Invalid format')

        self.PublicKey = ECDSA.Deserialize_Secp256r1(reader)

    def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        self.PublicKey.Serialize(writer, True)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        jsn = super(EnrollmentTransaction, self).ToJson()
        jsn['pubkey'] = self.PublicKey.ToString()
        return jsn
