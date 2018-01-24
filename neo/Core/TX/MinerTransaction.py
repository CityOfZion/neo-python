from neo.Core.TX.Transaction import Transaction, TransactionType
import sys
import binascii
from neocore.Fixed8 import Fixed8


class MinerTransaction(Transaction):
    Nonce = None

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(MinerTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.MinerTransaction

    def NetworkFee(self):
        """
        Get the network fee.

        Returns:
            Fixed8: currently fixed to 0.
        """

        return Fixed8(0)

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(MinerTransaction, self).Size() + sys.getsizeof(int)

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Nonce = reader.ReadUInt32()
        self.Type = TransactionType.MinerTransaction

    def SerializeExclusiveDataAlternative(self, writer):
        """
        Internal helper method.
        """
        byt = int.to_bytes(self.Nonce, 4, 'little')
        ba = bytearray(byt)
        byts = binascii.hexlify(ba)
        writer.WriteBytes(byts)

    def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        self.SerializeExclusiveDataAlternative(writer)

        # this should work, and it does in most cases
        # but for some reason with block 2992 on tesntet it doesnt
        # the nonce 1113941606 messes with it.
        # anyways, the above should work
        # writer.WriteUInt32(self.Nonce)

    def OnDeserialized(self):
        """
        Test deserialization success.

        Raises:
            Exception: if there are no inputs for the transaction.
        """
        if len(self.inputs) is not 0:
            raise Exception("No inputs for miner transaction")

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        jsn = super(MinerTransaction, self).ToJson()
        jsn['nonce'] = self.Nonce
        return jsn
