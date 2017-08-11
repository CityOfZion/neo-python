

from neo.Core.TX.Transaction import Transaction,TransactionType
import sys
from neo.Fixed8 import Fixed8

class InvocationTransaction(Transaction):


    Script = bytearray(0)
    Gas = Fixed8(0)

    def SystemFee(self):
        return Fixed8(self.Gas)



    def __init__(self, *args, **kwargs):
        super(InvocationTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.InvocationTransaction

    def Size(self):
        return self.Size() + sys.getsizeof(int)


    def DeserializeExclusiveData(self, reader):

        if self.Version > 1:
            raise Exception('Invalid format')

        self.Script = reader.ReadVarBytes()

        if len(self.Script) == 0:
            raise Exception('Invalid Format')

        if self.Version >= 1:
            self.Gas = reader.ReadFixed8()
        else:
            self.Gas = Fixed8(0)

    def SerializeExclusiveData(self, writer):
        writer.WriteVarBytes(self.Script)
        if self.Version >= 1:
            writer.WriteFixed8(self.Gas)


    def Verify(self, mempool):
        raise NotImplementedError()