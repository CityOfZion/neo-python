import unittest

from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.Transaction import Transaction
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
import binascii

class TransactionTestCase(unittest.TestCase):


    tx_raw = b'0000d11f7a2800000000'
    tx_raw_hex = binascii.unhexlify(tx_raw)

    tx_id = b'8e3a32ba3a7e8bdb0ad9a2ad064713e45bd20eb0dab0d2e77df5b5ce985276d0'
    tx_nonce = 679092177
    tx_vin = []
    tx_vout = []


    def test_tx_deserialize(self):

        ms = MemoryStream(self.tx_raw_hex)

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(type(tx), MinerTransaction )

        self.assertEqual(tx.HashToString(), self.tx_id)

        self.assertEqual(tx.Nonce, self.tx_nonce)

        self.assertEqual(tx.inputs, [])
        self.assertEqual(tx.outputs, [])
        self.assertEqual(tx.scripts, [])


        ms = MemoryStream()
        writer = BinaryWriter(ms)

        tx.Serialize(writer)
        out = ms.ToArray()

        self.assertEqual(out, self.tx_raw)
