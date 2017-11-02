

from neo.Core.TX.Transaction import Transaction, TransactionType
import sys
import binascii
from neo.Cryptography.ECCurve import EllipticCurve, ECDSA
from neo.Settings import settings
from neo.Fixed8 import Fixed8


class EnrollmentTransaction(Transaction):

    PublicKey = None
    _script_hash = None

    def __init__(self, *args, **kwargs):
        super(EnrollmentTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.EnrollmentTransaction

    def Size(self):
        return self.Size() + sys.getsizeof(int)

    def SystemFee(self):
        return Fixed8(int(settings.ENROLLMENT_TX_FEE))

    def DeserializeExclusiveData(self, reader):
        if self.Version is not 0:
            raise Exception('Invalid format')

        self.PublicKey = ECDSA.Deserialize_Secp256r1(reader)

    def SerializeExclusiveData(self, writer):
        self.PublicKey.Serialize(writer, True)

    def ToJson(self):
        jsn = super(EnrollmentTransaction, self).ToJson()
        jsn['pubkey'] = self.PublicKey.ToString()
        return jsn
