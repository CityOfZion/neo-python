

from neo.Core.TX.Transaction import Transaction, TransactionType
import sys
import binascii
from neo.Fixed8 import Fixed8


class MinerTransaction(Transaction):

    Nonce = None

    def __init__(self, *args, **kwargs):
        super(MinerTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.MinerTransaction

    def NetworkFee(self):
        return Fixed8(0)

    def Size(self):
        return self.Size() + sys.getsizeof(int)

    def DeserializeExclusiveData(self, reader):
        self.Nonce = reader.ReadUInt32()
        self.Type = TransactionType.MinerTransaction

    def SerializeExclusiveDataAlternative(self, writer):
        byt = int.to_bytes(self.Nonce, 4, 'little')
        ba = bytearray(byt)
        byts = binascii.hexlify(ba)
        writer.WriteBytes(byts)

    def SerializeExclusiveData(self, writer):
        self.SerializeExclusiveDataAlternative(writer)

        # this should work, and it does in most cases
        # but for some reason with block 2992 on tesntet it doesnt
        # the nonce 1113941606 messes with it.
        # anyways, the above should work
        # writer.WriteUInt32(self.Nonce)

    def OnDeserialized(self):
        if len(self.inputs) is not 0:
            raise Exception("No inputs for miner transaction")

    def ToJson(self):
        jsn = super(MinerTransaction, self).ToJson()
        jsn['nonce'] = self.Nonce
        return jsn
