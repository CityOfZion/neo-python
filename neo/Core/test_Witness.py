import binascii
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Core.Witness import Witness
from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from io import BytesIO


class WitnessTest(NeoTestCase):
    raw_witness = binascii.unhexlify(
        '414009f116ea749e5238b5d37b0db3ad939c2187df05d33a9b8088e32ccd54a56a07e7a946f72c4eb76b1e6372db43fdbfc13a8f4f64dcfeb8ee23a4de721d518ab4232103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699ac')
    invoc_len = '41'
    expected_Script_InvocationScript = binascii.unhexlify(
        '4009f116ea749e5238b5d37b0db3ad939c2187df05d33a9b8088e32ccd54a56a07e7a946f72c4eb76b1e6372db43fdbfc13a8f4f64dcfeb8ee23a4de721d518ab4')

    verif_len = '23'
    expected_Script_VerificationScript = binascii.unhexlify(
        '2103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699ac')
    expected_size = 102

    def test_toJSON(self):
        PUSHT = b'\x51'

        # taken from GenesisBlockTestCase.test_issue_tx
        w = Witness(bytearray(0), bytearray(PUSHT))
        data = w.ToJson()
        self.assertTrue('invocation' in data)
        self.assertTrue('verification' in data)
        self.assertEqual(len(binascii.unhexlify(data['invocation'])), 0)
        self.assertEqual(len(binascii.unhexlify(data['verification'])), 1)

    def test_toJSON_empty_witness(self):
        w = Witness()
        data = w.ToJson()
        self.assertTrue('invocation' in data)
        self.assertTrue('verification' in data)
        self.assertEqual(len(data['invocation']), 0)
        self.assertEqual(len(data['verification']), 0)

    def test_deserialization(self):
        stream = StreamManager.GetStream(self.raw_witness)
        reader = BinaryReader(stream)

        w = Witness()
        w.Deserialize(reader)
        self.assertEqual(w.InvocationScript,
                         self.expected_Script_InvocationScript)
        self.assertEqual(w.VerificationScript,
                         self.expected_Script_VerificationScript)

        data = w.ToJson()
        self.assertTrue('invocation' in data)
        self.assertTrue('verification' in data)
        self.assertEqual(len(binascii.unhexlify(data['invocation'])), 0x41)
        self.assertEqual(len(binascii.unhexlify(data['verification'])), 0x23)

    def test_serialization(self):
        stream = StreamManager.GetStream(self.raw_witness)
        reader = BinaryReader(stream)

        w = Witness()
        w.Deserialize(reader)

        writestream = BytesIO()
        writer = BinaryWriter(writestream)

        w.Serialize(writer)
        data = writestream.getvalue()
        self.assertEqual(data, self.raw_witness)

    def test_size(self):
        stream = StreamManager.GetStream(self.raw_witness)
        reader = BinaryReader(stream)

        w = Witness()
        w.Deserialize(reader)

        self.assertEqual(w.Size(), self.expected_size)

    def test_invalid_invocation_script(self):
        invalid_script = 'aabb'
        with self.assertRaises(ValueError) as context:
            Witness(invocation_script=invalid_script, verification_script=bytearray(0))
        self.assertTrue("Invalid invocation_script parameter " in str(context.exception))

    def test_invalid_verification_script(self):
        invalid_script = 'aabb'
        with self.assertRaises(ValueError) as context:
            Witness(invocation_script=bytearray(0), verification_script=invalid_script)
        self.assertTrue("Invalid verification_script parameter " in str(context.exception))

    def test_parameters_already_raw_bytes(self):
        """Test proper assignment when the value in invocation_script is already in raw bytes """
        raw_bytes = b'\x51\xAA'
        w = Witness(verification_script=raw_bytes, invocation_script=raw_bytes)
        self.assertEqual(w.VerificationScript, raw_bytes)
        self.assertEqual(w.InvocationScript, raw_bytes)
