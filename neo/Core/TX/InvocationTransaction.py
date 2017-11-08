

from neo.Core.TX.Transaction import Transaction, TransactionType
import sys
from neo.Fixed8 import Fixed8


class InvocationTransaction(Transaction):

    Script = None
    Gas = None

    def SystemFee(self):
        return self.Gas // Fixed8.FD()

    def __init__(self, *args, **kwargs):
        super(InvocationTransaction, self).__init__(*args, **kwargs)
        self.Gas = Fixed8(0)
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
            if self.Gas < Fixed8.Zero():
                raise Exception("Invalid Format")
        else:
            self.Gas = Fixed8(0)

    def SerializeExclusiveData(self, writer):
        writer.WriteVarBytes(self.Script)
        if self.Version >= 1:
            writer.WriteFixed8(self.Gas)

    def Verify(self, mempool):
        if self.Gas.value % 100000000 != 0:
            return False
        return super(InvocationTransaction, self).Verify(mempool)

    def ToJson(self):
        jsn = super(InvocationTransaction, self).ToJson()
        jsn['script'] = self.Script.hex()
        jsn['gas'] = self.Gas.value
        return jsn
