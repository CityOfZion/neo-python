
import unittest
from neo.Blockchain import GetGenesis
import binascii
from neo.IO.Helper import Helper

from neo.Cryptography.MerkleTree import MerkleTree

class BlocksTestCase(unittest.TestCase):


    #raw block ( block # 343892 )
    rawblock = b'00000000b7def681f0080262aa293071c53b41fc3146b196067243700b68acd059734fd19543108bf9ddc738cbee2ed1160f153aa0d057f062de0aa3cbb64ba88735c23d43667e59543f050095df82b02e324c5ff3812db982f3b0089a21a278988efeec6a027b2501fd450140113ac66657c2f544e8ad13905fcb2ebaadfef9502cbefb07960fbe56df098814c223dcdd3d0efa0b43a9459e654d948516dcbd8b370f50fbecfb8b411d48051a408500ce85591e516525db24065411f6a88f43de90fa9c167c2e6f5af43bc84e65e5a4bb174bc83a19b6965ff10f476b1b151ae15439a985f33916abc6822b0bb140f4aae522ffaea229987a10d01beec826c3b9a189fe02aa82680581b78f3df0ea4d3f93ca8ea35ffc90f15f7db9017f92fafd9380d9ba3237973cf4313cf626fc40e30e50e3588bd047b39f478b59323868cd50c7ab54355d8245bf0f1988d37528f9bbfc68110cf917debbdbf1f4bdd02cdcccdc3269fdf18a6c727ee54b6934d840e43918dd1ec6123550ec37a513e72b34b2c2a3baa510dec3037cbef2fa9f6ed1e7ccd1f3f6e19d4ce2c0919af55249a970c2685217f75a5589cf9e54dff8449af155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae01000095df82b000000000'

    rawblock_hex = b'\x00\x00\x00\x00\xb7\xde\xf6\x81\xf0\x08\x02b\xaa)0q\xc5;A\xfc1F\xb1\x96\x06rCp\x0bh\xac\xd0YsO\xd1\x95C\x10\x8b\xf9\xdd\xc78\xcb\xee.\xd1\x16\x0f\x15:\xa0\xd0W\xf0b\xde\n\xa3\xcb\xb6K\xa8\x875\xc2=Cf~YT?\x05\x00\x95\xdf\x82\xb0.2L_\xf3\x81-\xb9\x82\xf3\xb0\x08\x9a!\xa2x\x98\x8e\xfe\xecj\x02{%\x01\xfdE\x01@\x11:\xc6fW\xc2\xf5D\xe8\xad\x13\x90_\xcb.\xba\xad\xfe\xf9P,\xbe\xfb\x07\x96\x0f\xbeV\xdf\t\x88\x14\xc2#\xdc\xdd=\x0e\xfa\x0bC\xa9E\x9eeM\x94\x85\x16\xdc\xbd\x8b7\x0fP\xfb\xec\xfb\x8bA\x1dH\x05\x1a@\x85\x00\xce\x85Y\x1eQe%\xdb$\x06T\x11\xf6\xa8\x8fC\xde\x90\xfa\x9c\x16|.oZ\xf4;\xc8Ne\xe5\xa4\xbb\x17K\xc8:\x19\xb6\x96_\xf1\x0fGk\x1b\x15\x1a\xe1T9\xa9\x85\xf39\x16\xab\xc6\x82+\x0b\xb1@\xf4\xaa\xe5"\xff\xae\xa2)\x98z\x10\xd0\x1b\xee\xc8&\xc3\xb9\xa1\x89\xfe\x02\xaa\x82h\x05\x81\xb7\x8f=\xf0\xeaM?\x93\xca\x8e\xa3_\xfc\x90\xf1_}\xb9\x01\x7f\x92\xfa\xfd\x93\x80\xd9\xba27\x97<\xf41<\xf6&\xfc@\xe3\x0eP\xe3X\x8b\xd0G\xb3\x9fG\x8bY28h\xcdP\xc7\xabT5]\x82E\xbf\x0f\x19\x88\xd3u(\xf9\xbb\xfch\x11\x0c\xf9\x17\xde\xbb\xdb\xf1\xf4\xbd\xd0,\xdc\xcc\xdc2i\xfd\xf1\x8alr~\xe5Ki4\xd8@\xe49\x18\xdd\x1e\xc6\x125P\xec7\xa5\x13\xe7+4\xb2\xc2\xa3\xba\xa5\x10\xde\xc3\x03|\xbe\xf2\xfa\x9fn\xd1\xe7\xcc\xd1\xf3\xf6\xe1\x9dL\xe2\xc0\x91\x9a\xf5RI\xa9p\xc2hR\x17\xf7ZU\x89\xcf\x9eT\xdf\xf8D\x9a\xf1U!\x02\t\xe7\xfdA\xdf\xb5\xc2\xf8\xdcr\xeb05\x8a\xc1\x00\xea\x8cr\xda\x18\x84{\xef\xe0n\xad\xe6\x8c\xeb\xfc\xb9!\x03\'\xda\x12\xb5\xc4\x02\x00\xe9\xf6UiGk\xbf\xf2!\x8d\xa4\xf3%H\xffC\xb68~\xc1Aj#\x1e\xe8!\x03O\xf5\xce\xea\xc4\x1a\xcf"\xcd^\xd2\xda\x17\xa6\xdfM\xd85\x8f\xcb+\xfb\x1aC \x8a\xd0\xfe\xaa\xb2tk!\x02l\xe3[)\x14z\xd0\x9eJ\xfeN\xc4\xa71\x90\x95\xf0\x81\x98\xfa\x8b\xab\xbe<V\xe9p\xb1CR\x8d"!\x03\x8d\xdd\xc0l\xe6\x87gzS\xd5O\tm%\x91\xba#\x02\x06\x8c\xf1#\xc1\xf2\xd7\\-\xdd\xc5BUy!\x03\x9d\xaf\xd8W\x1ad\x10X\xcc\xc82\xc5\xe2\x11\x1e\xa3\x9b\t\xc0\xbd\xe3`P\x91C\x84\xf7\xa4\x8b\xce\x9b\xf9!\x02\xd0+\x18s\xa0\x86<\xd0B\xccq}\xa3\x1c\xea\r|\xf9\xdb2\xb7MLr\xc0\x1b\x00\x11P>."W\xae\x01\x00\x00\x95\xdf\x82\xb0\x00\x00\x00\x00'
    rb_hash=b'922ba0c0d06afbeec4c50b0541a29153feaa46c5d7304e7bf7f40870d9f3aeb0'
    rb_prev=b'd14f7359d0ac680b7043720696b14631fc413bc5713029aa620208f081f6deb7'
    rb_merlke=b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
    rb_ts = 1501455939
    rb_h = 343892
    rb_nonce = int.from_bytes( binascii.unhexlify( b'5f4c322eb082df95'), 'big')
    rconsenusdata = 6866918707944415125

    rblock_tx_id = b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
    rblock_tx_nonce=2961366933
    rblock_inputs = []
    rblock_outputs = []

    #raw block 2 ( block #1)
    b2raw = b'00000000ef1f8f66a16fba100ed760f4ac6aa5a0d0bb8f4a0e92705b106761ef181718b3d0765298ceb5f57de7d2b0dab00ed25be4134706ada2d90adb8b7e3aba323a8e1abd125901000000d11f7a289214bdaff3812db982f3b0089a21a278988efeec6a027b2501fd450140884037dd265cb5f5a54802f53c2c8593b31d5b8a9c0bad4c7e366b153d878989d168080ac36b930036a9eb966b48c70bb41792e698fa021116f27c09643563b840e83ab14404d964a91dbac45f5460e88ad57196b1779478e3475334af8c1b49cd9f0213257895c60b5b92a4800eb32d785cbb39ae1f022528943909fd37deba63403677848bf98cc9dbd8fbfd7f2e4f34471866ea82ca6bffbf0f778b6931483700c17829b4bd066eb04983d3aac0bd46b9c8d03a73a8e714d3119de93cd9522e314054d16853b22014190063f77d9edf6fbccefcf71fffd1234f688823b4e429ae5fa639d0a664c842fbdfcb4d6e21f39d81c23563b92cffa09696d93c95bc4893a6401a43071d00d3e854f7f1f321afa7d5301d36f2195dc1e2643463f34ae637d2b02ae0eb11d4256c507a4f8304cea6396a7fce640f50acb301c2f6336d27717e84f155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae010000d11f7a2800000000'
    b2hash = '0012f8566567a9d7ddf25acb5cf98286c9703297de675d01ba73fbfe6bcb841c'
    b2prev_hash = b'b3181718ef6167105b70920e4a8fbbd0a0a56aacf460d70e10ba6fa1668f1fef'
    b2height = 1
    b2merkle = '8e3a32ba3a7e8bdb0ad9a2ad064713e45bd20eb0dab0d2e77df5b5ce985276d0'
    b2nonce = int.from_bytes(binascii.unhexlify('afbd1492287a1fd1'), 'big')
    b2nextconsensus = 'AdyQbbn6ENjqWDa5JNYMwN3ikNcA4JeZdk'
    b2timestamp = 1494400282

    b2invocation = b'40884037dd265cb5f5a54802f53c2c8593b31d5b8a9c0bad4c7e366b153d878989d168080ac36b930036a9eb966b48c70bb41792e698fa021116f27c09643563b840e83ab14404d964a91dbac45f5460e88ad57196b1779478e3475334af8c1b49cd9f0213257895c60b5b92a4800eb32d785cbb39ae1f022528943909fd37deba63403677848bf98cc9dbd8fbfd7f2e4f34471866ea82ca6bffbf0f778b6931483700c17829b4bd066eb04983d3aac0bd46b9c8d03a73a8e714d3119de93cd9522e314054d16853b22014190063f77d9edf6fbccefcf71fffd1234f688823b4e429ae5fa639d0a664c842fbdfcb4d6e21f39d81c23563b92cffa09696d93c95bc4893a6401a43071d00d3e854f7f1f321afa7d5301d36f2195dc1e2643463f34ae637d2b02ae0eb11d4256c507a4f8304cea6396a7fce640f50acb301c2f6336d27717e84'
    b2verification = b'55210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae'

    b2tx_len = 1

    b2tx_id = b'8e3a32ba3a7e8bdb0ad9a2ad064713e45bd20eb0dab0d2e77df5b5ce985276d0'
    b2tx_nonce = 679092177
    b2tx_vin = []
    b2tx_vout = []


    @staticmethod
    def BlockIndexOne():
        print("GETTING BLOCK INDEX ONE!")
        block = Helper.AsSerializableWithType(BlocksTestCase.b2raw, 'neo.Core.Block.Block')
        return block

    def test_block_deserialize(self):

        block = Helper.AsSerializableWithType(self.rawblock_hex, 'neo.Core.Block.Block')

        self.assertEqual(self.rb_prev, block.PrevHash)
        self.assertEqual(self.rb_merlke, block.MerkleRoot)
        self.assertEqual(self.rb_ts, block.Timestamp)
        self.assertEqual(self.rb_h, block.Index)
        self.assertEqual(self.rb_nonce, block.ConsensusData)
        self.assertEqual(self.rconsenusdata, block.ConsensusData)
#        self.assertEqual(self.rb_hash, block.HashToString())
        tx = block.Transactions[0]

        self.assertEqual(tx.Nonce, self.rblock_tx_nonce)


        self.assertEqual(len(tx.inputs), 0)
        self.assertEqual(len(tx.outputs), 0)
        self.assertEqual(len(tx.Attributes), 0)

        self.assertEqual(type(tx.scripts), list)

        rawdata = block.RawData()
        compair_data = self.rawblock[:len(rawdata)]
        self.assertEqual(rawdata, compair_data)
        out = bytes(block.HashToString().encode('utf-8'))
        self.assertEqual(out, self.rb_hash)

        root = MerkleTree.ComputeRoot([tx.HashToString() for tx in block.Transactions])
        self.assertEqual(root, block.MerkleRoot)



    def test_block_two(self):
        hexdata = binascii.unhexlify(self.b2raw)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')
        self.assertEqual(block.Index, self.b2height)
        self.assertEqual(block.ConsensusData, self.b2nonce)
        self.assertEqual(block.Timestamp, self.b2timestamp)
        self.assertEqual(block.PrevHash, self.b2prev_hash)


        self.assertEqual(block.HashToString(), self.b2hash)

        next_consensus_address = block.NextConsensusToWalletAddress()

        self.assertEqual(next_consensus_address, self.b2nextconsensus)

        witness = block.Script
        ins = binascii.hexlify(witness.InvocationScript)
        vns = binascii.hexlify(witness.VerificationScript)

        self.assertEqual(ins, self.b2invocation)
        self.assertEqual(vns, self.b2verification)
        self.assertEqual(len(block.Transactions), self.b2tx_len)

        tx = block.Transactions[0]

        self.assertEqual(tx.inputs, self.b2tx_vin)
        self.assertEqual(tx.outputs, self.b2tx_vout)

        self.assertEqual(tx.Nonce, self.b2tx_nonce)

        txhash = tx.HashToString()
        self.assertEqual(txhash, self.b2tx_id)

        root = MerkleTree.ComputeRoot([tx.HashToString() for tx in block.Transactions])
        self.assertEqual(root, block.MerkleRoot)

