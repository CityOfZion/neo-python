

from neo.Core.TX.Transaction import Transaction,TransactionType
import sys
import binascii

class EnrollmentTransaction(Transaction):

    PublicKey = None
    _script_hash = None



    def __init__(self, *args, **kwargs):
        super(EnrollmentTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.EnrollmentTransaction

    def Size(self):
        return self.Size() + sys.getsizeof(int)

    def DeserializeExclusiveData(self, reader):
        if self.Version is not 0:
            raise Exception('Invalid format')

        self.PublicKey = reader.ReadBytes(33)

    def SerializeExclusiveData(self, writer):
        writer.WriteBytes(self.PublicKey)


