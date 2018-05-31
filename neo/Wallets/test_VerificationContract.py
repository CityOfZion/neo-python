import binascii
from io import BytesIO
from neo.Utils.NeoTestCase import NeoTestCase
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Wallets.VerificationContract import VerificationContract
from neo.SmartContract.ContractParameterType import ContractParameterType
from neocore.KeyPair import KeyPair


class VerificationContractTest(NeoTestCase):
    # Captured data from C# client 2.4.1.0
    raw_verification_contract = binascii.unhexlify(
        '27fd098f9ffc3309fbc310cccfde9a9fb445a8790100232102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406eac')
    expected_address = 'AWLYWXB8C9Lt1nHdDZJnC5cpYJjgRDLk17'
    expected_isStandard = True
    expected_ParameterList = [bytes([ContractParameterType.Signature.value])]
    expected_PublicKeyHash = '79a845b49f9adecfcc10c3fb0933fc9f8f09fd27'
    expected_Script = bytes.fromhex(
        '2102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406eac')
    expected_ScriptHash = '7e309b2eb493576ffee1de2dc56bef203383bf9f'
    expected_size = 58

    def test_Deserialization(self):
        stream = StreamManager.GetStream(self.raw_verification_contract)
        reader = BinaryReader(stream)

        vct = VerificationContract()
        vct.Deserialize(reader)

        self.assertEqual(vct.Address, self.expected_address)
        self.assertEqual(vct.IsStandard, self.expected_isStandard)
        self.assertEqual(vct.ParameterList, self.expected_ParameterList)
        self.assertEqual(vct.PublicKeyHash.ToString(),
                         self.expected_PublicKeyHash)
        self.assertEqual(vct.Script, self.expected_Script)
        self.assertEqual(vct.ScriptHash.ToString(), self.expected_ScriptHash)
        self.assertEqual(vct.Size(), self.expected_size)

    def test_serialization(self):
        stream = StreamManager.GetStream(self.raw_verification_contract)
        reader = BinaryReader(stream)

        vct = VerificationContract()
        vct.Deserialize(reader)

        writestream = BytesIO()
        writer = BinaryWriter(writestream)

        vct.Serialize(writer)
        data = writestream.getvalue()
        self.assertEqual(data, self.raw_verification_contract)

    def test_isStandard_failures(self):
        stream = StreamManager.GetStream(self.raw_verification_contract)
        reader = BinaryReader(stream)

        vct = VerificationContract()
        vct.Deserialize(reader)

        # to fail specific byte tests
        script = list(vct.Script)
        script[0] = 0  # != 33
        vct.Script = bytes(script)
        self.assertFalse(vct.IsStandard)

        # to fail length test
        vct.Script = vct.Script[:-1]
        self.assertFalse(vct.IsStandard)

    def test_CreateSignatureContract(self):
        wif_wallet2 = 'KzfPUYDC9n2yf4fK5ro4C8KMcdeXtFuEnStycbZgX3GomiUsvX6W'
        priv = KeyPair.PrivateKeyFromWIF(wif_wallet2)
        kp = KeyPair(priv_key=priv)

        output = VerificationContract.CreateSignatureContract(kp.PublicKey)
        self.assertEqual(output.PublicKeyHash.ToString(),
                         self.expected_PublicKeyHash)
        self.assertEqual(output.Script, self.expected_Script)
        self.assertEqual(output.Address, self.expected_address)
