import binascii
from io import BytesIO
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Network.Payloads.ConsensusPayload import ConsensusPayload
from neo.Core.Witness import Witness
from neo.Network.Payloads.ConsensusPayload import InvalidOperationException
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from threading import Lock
from neocore.KeyPair import KeyPair
from mock import patch
from neo.Settings import settings
import os


def build_validator_list():
    # fix the consensus validators to the privnet nodes
    wif_wallet1 = 'KxyjQ8eUa4FHt3Gvioyt1Wz29cTUrE4eTqX3yFSk1YFCsPL8uNsY'
    wif_wallet2 = 'KzfPUYDC9n2yf4fK5ro4C8KMcdeXtFuEnStycbZgX3GomiUsvX6W'
    wif_wallet3 = 'L2oEXKRAAMiPEZukwR5ho2S6SMeQLhcK9mF71ZnF7GvT8dU4Kkgz'
    wif_wallet4 = 'KzgWE3u3EDp13XPXXuTKZxeJ3Gi8Bsm8f9ijY3ZsCKKRvZUo1Cdn'
    wallets = [wif_wallet2, wif_wallet4, wif_wallet1, wif_wallet3]

    validators = []
    for w in wallets:
        priv = KeyPair.PrivateKeyFromWIF(w)
        kp = KeyPair(priv_key=priv)
        validators.append(kp.PublicKey)

    return validators


class ConsensusPayloadTest(BlockchainFixtureTestCase):
    # Captured from neo C# client 2.4.1.0
    consensus_payload_raw = binascii.unhexlify(
        '0000000083144b120bc7f93128f9e22d3bb5a7d0428552ea538edb2199ad4afef0b4684813000000030046853a5a892000417cbdc9b4a969d9be48d3a3f5d10013ab9ffee489706078714f1ea20120acbda7fdf127f5c045b38911c4b47f91ebfe661eadb3c8557a1c31f06df5d20000417cbdc9000000005b3babb75212701a561d31d3a746e79a2cc0ac6a3b638e345aa6f978ac8e1c973b46bc46c12d085ca97872087ff4e630e44f579894e967d8bfef81be687485bc01414009f116ea749e5238b5d37b0db3ad939c2187df05d33a9b8088e32ccd54a56a07e7a946f72c4eb76b1e6372db43fdbfc13a8f4f64dcfeb8ee23a4de721d518ab4232103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699ac')
    expected_BlockIndex = 19
    expected_Data = bytes.fromhex(
        '2000417cbdc9b4a969d9be48d3a3f5d10013ab9ffee489706078714f1ea20120acbda7fdf127f5c045b38911c4b47f91ebfe661eadb3c8557a1c31f06df5d20000417cbdc9000000005b3babb75212701a561d31d3a746e79a2cc0ac6a3b638e345aa6f978ac8e1c973b46bc46c12d085ca97872087ff4e630e44f579894e967d8bfef81be687485bc')
    expected_PrevHash = '4868b4f0fe4aad9921db8e53ea528542d0a7b53b2de2f92831f9c70b124b1483'
    expected_Script_InvocationScript = binascii.unhexlify(
        '4009f116ea749e5238b5d37b0db3ad939c2187df05d33a9b8088e32ccd54a56a07e7a946f72c4eb76b1e6372db43fdbfc13a8f4f64dcfeb8ee23a4de721d518ab4')
    expected_Script_VerificationScript = binascii.unhexlify(
        '2103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699ac')
    expected_Script_Size = 102
    expected_Size = 287
    expected_Version = 0
    expected_ValidatorIndex = 3
    expected_Timestamp = 1513784646
    expected__hash = '5ca2c09df092bc5f276ac04dbbe585483fa1287c4de4c937012e814b4b7a668c'
    expected_GetHashData = '0000000083144b120bc7f93128f9e22d3bb5a7d0428552ea538edb2199ad4afef0b4684813000000030046853a5a892000417cbdc9b4a969d9be48d3a3f5d10013ab9ffee489706078714f1ea20120acbda7fdf127f5c045b38911c4b47f91ebfe661eadb3c8557a1c31f06df5d20000417cbdc9000000005b3babb75212701a561d31d3a746e79a2cc0ac6a3b638e345aa6f978ac8e1c973b46bc46c12d085ca97872087ff4e630e44f579894e967d8bfef81be687485bc'
    expected_Hash256_of_GetHashData = '8c667a4b4b812e0137c9e44d7c28a13f4885e5bb4dc06a275fbc92f09dc0a25c'
    expected_single_hash256 = '6256c3905e0b13c1bc365447639eafbb40a1108f51f489ff68d546b6c74099fe'
    GetScripthashesforverifying_result = '6c45d212115a56fbfb7699730a2608fd991dc165'
    verify_result = True
    expected_GetMessage = '0000000083144b120bc7f93128f9e22d3bb5a7d0428552ea538edb2199ad4afef0b4684813000000030046853a5a892000417cbdc9b4a969d9be48d3a3f5d10013ab9ffee489706078714f1ea20120acbda7fdf127f5c045b38911c4b47f91ebfe661eadb3c8557a1c31f06df5d20000417cbdc9000000005b3babb75212701a561d31d3a746e79a2cc0ac6a3b638e345aa6f978ac8e1c973b46bc46c12d085ca97872087ff4e630e44f579894e967d8bfef81be687485bc'

    _blockchain = None

    lock = Lock()

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_consensus.tar.gz'
    FIXTURE_FILENAME = './Chains/fixtures_consensus.tar.gz'

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/consensus1')

    def setUp(self):
        self.stream = StreamManager.GetStream(self.consensus_payload_raw)
        reader = BinaryReader(self.stream)

        self.cp = ConsensusPayload()
        self.cp.Deserialize(reader)

    def tearDown(self):
        StreamManager.ReleaseStream(self.stream)

    def test_01_blockheight(self):
        with self.lock:
            current_height = len(self._blockchain._header_index) - 1
            self.assertEqual(current_height, 92)

    def test_02_deserialization(self):
        cp = self.cp

        self.assertEqual(cp.BlockIndex, self.expected_BlockIndex)
        self.assertEqual(cp.Data, self.expected_Data)
        self.assertEqual(cp.PrevHash.ToString(), self.expected_PrevHash)
        self.assertEqual(cp.Script.InvocationScript,
                         self.expected_Script_InvocationScript)
        self.assertEqual(cp.Script.VerificationScript,
                         self.expected_Script_VerificationScript)
        self.assertEqual(cp.Script.Size(), self.expected_Script_Size)
        self.assertEqual(cp.Size(), self.expected_Size)
        self.assertEqual(cp.Version, self.expected_Version)
        self.assertEqual(cp.ValidatorIndex, self.expected_ValidatorIndex)
        self.assertEqual(cp.Timestamp, self.expected_Timestamp)
        self.assertEqual(cp.Hash.ToString(), self.expected__hash)

    def test_03_deserialization_failure(self):
        wrong_format = "AA"  # should be 01 to be valid
        consensus_payload_edited = binascii.unhexlify(
            "00000000ff306cfd03b99e9525cd1c2e6d02d5fcb5e2f1ddf2eecc41827476f3267fc7e74c01000000003c8c395a03000002" + wrong_format + "414066b56923f905c16f9da506ca0ac583b1f72d102b5a90dd0298f2a85d78e011442b260b19ccbd43b2cf9bbd9df651fd9d4ac5a4aa70e0603741c535c28e75f5bd232102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406eac")
        stream = StreamManager.GetStream(consensus_payload_edited)
        reader = BinaryReader(stream)

        cp = ConsensusPayload()
        self.assertRaises(Exception, cp.Deserialize, reader)

    def test_04_serialization(self):
        cp = self.cp

        writestream = BytesIO()
        writer = BinaryWriter(writestream)

        cp.Serialize(writer)
        data = writestream.getvalue()
        self.assertEqual(data, self.consensus_payload_raw)

    def test_05_GetMessage_and_GetHashData(self):
        cp = self.cp

        self.assertEqual(cp.GetMessage().decode(
            'utf8'), self.expected_GetMessage)
        # internally they call the same method
        self.assertEqual(cp.GetHashData().decode(
            'utf8'), self.expected_GetMessage)

    def test_06_Scripts(self):
        cp = ConsensusPayload()
        w = Witness()
        cp.Scripts = [w]

        self.assertEqual(cp.Scripts[0], w)
        self.assertEqual(cp.Script, w)

        with self.assertRaises(ValueError) as context:
            cp.Scripts = []
        self.assertTrue(
            'expect value to be a list of length 1' in str(context.exception))

        with self.assertRaises(ValueError) as context:
            cp.Scripts = [None]
        self.assertTrue(
            'List item is not a Witness object' in str(context.exception))

    @patch('neo.Core.Blockchain.Blockchain.GetValidators')
    def test_07_verify_scripts(self, mocked_GetValidators):
        cp = self.cp
        mocked_GetValidators.return_value = build_validator_list()

        with self.lock:
            self._blockchain._current_block_height = cp.BlockIndex - 1

            self.assertTrue(cp.Verify())

            # set to a block index that doesn't match the payload should lead to wrong hashes
            self._blockchain._current_block_height = 1
            self.assertFalse(cp.Verify())

            # test failing BlockHeight match
            # first restore Blockchain's block_height to the correct value
            self._blockchain._current_block_height = cp.BlockIndex - 1

            # then set payload BlockIndex to a wrong value
            cp.BlockIndex = 1
            self.assertFalse(cp.Verify())

    @patch('neo.Core.Blockchain.Blockchain.GetValidators')
    def test_08_GetScriptHashesForVerifying(self, mocked_GetValidators):
        cp = self.cp
        mocked_GetValidators.return_value = build_validator_list()

        with self.lock:
            # explicitely set blockchain block height
            self._blockchain._current_block_height = 1
            with self.assertRaises(InvalidOperationException) as context:
                cp.GetScriptHashesForVerifying()
            self.assertTrue(
                "PrevHash != CurrentBlockHash" in str(context.exception))

            # test validator array length mismatch
            # first restore the block index for the PrevHash check
            self._blockchain._current_block_height = cp.BlockIndex - 1
            # then make our payload index exceed the validator count
            cp.ValidatorIndex = 100
            with self.assertRaises(InvalidOperationException) as context:
                cp.GetScriptHashesForVerifying()
            self.assertTrue(
                "ValidatorIndex out of range" in str(context.exception))
