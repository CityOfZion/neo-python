

from neo.Core.TX.Transaction import Transaction,TransactionType
import sys
from neo.Fixed8 import Fixed8

class InvocationTransaction(Transaction):


    Script = bytearray(0)
    Gas = 0

    def SystemFee(self):
        return self.Gas



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
            fval = reader.ReadInt64()
            self.Gas = Fixed8(int(fval))
        else:
            self.Gas = Fixed8(0)

    def SerializeExclusiveData(self, writer):
        writer.WriteVarBytes(self.Script)
        if self.Version >= 1:
            writer.WriteInt64(int(self.Gas.value))


    def Verify(self, mempool):
        raise NotImplementedError()