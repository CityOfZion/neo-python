

from AntShares.Core.Transaction import Transaction
import sys

class MinerTransaction(Transaction):

    Nonce = None

    NetworkFee = 0

    def Size(self):
        return self.Size() + sys.getsizeof(int)

    def DeserializeExclusiveData(self, reader):
        self.Nonce = reader.readUInt32()


    def OnDeserialized(self):
        raise NotImplementedError()
