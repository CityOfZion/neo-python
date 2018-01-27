from neo.Utils.NeoTestCase import NeoTestCase
import os
import binascii
from neo.IO.Helper import Helper
from neo.Core.Block import Block
from neocore.Cryptography.Crypto import Crypto
from neocore.Cryptography.MerkleTree import MerkleTree
from neocore.Fixed8 import Fixed8
from neo.Core.TX.StateTransaction import StateTransaction
from neo.Core.State.StateDescriptor import StateDescriptor, StateType


class BlocksTestCase(NeoTestCase):

    # raw block ( block # 343892 )
    rawblock = b'00000000b7def681f0080262aa293071c53b41fc3146b196067243700b68acd059734fd19543108bf9ddc738cbee2ed1160f153aa0d057f062de0aa3cbb64ba88735c23d43667e59543f050095df82b02e324c5ff3812db982f3b0089a21a278988efeec6a027b2501fd450140113ac66657c2f544e8ad13905fcb2ebaadfef9502cbefb07960fbe56df098814c223dcdd3d0efa0b43a9459e654d948516dcbd8b370f50fbecfb8b411d48051a408500ce85591e516525db24065411f6a88f43de90fa9c167c2e6f5af43bc84e65e5a4bb174bc83a19b6965ff10f476b1b151ae15439a985f33916abc6822b0bb140f4aae522ffaea229987a10d01beec826c3b9a189fe02aa82680581b78f3df0ea4d3f93ca8ea35ffc90f15f7db9017f92fafd9380d9ba3237973cf4313cf626fc40e30e50e3588bd047b39f478b59323868cd50c7ab54355d8245bf0f1988d37528f9bbfc68110cf917debbdbf1f4bdd02cdcccdc3269fdf18a6c727ee54b6934d840e43918dd1ec6123550ec37a513e72b34b2c2a3baa510dec3037cbef2fa9f6ed1e7ccd1f3f6e19d4ce2c0919af55249a970c2685217f75a5589cf9e54dff8449af155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae01000095df82b000000000'

    rawblock_hex = b'\x00\x00\x00\x00\xb7\xde\xf6\x81\xf0\x08\x02b\xaa)0q\xc5;A\xfc1F\xb1\x96\x06rCp\x0bh\xac\xd0YsO\xd1\x95C\x10\x8b\xf9\xdd\xc78\xcb\xee.\xd1\x16\x0f\x15:\xa0\xd0W\xf0b\xde\n\xa3\xcb\xb6K\xa8\x875\xc2=Cf~YT?\x05\x00\x95\xdf\x82\xb0.2L_\xf3\x81-\xb9\x82\xf3\xb0\x08\x9a!\xa2x\x98\x8e\xfe\xecj\x02{%\x01\xfdE\x01@\x11:\xc6fW\xc2\xf5D\xe8\xad\x13\x90_\xcb.\xba\xad\xfe\xf9P,\xbe\xfb\x07\x96\x0f\xbeV\xdf\t\x88\x14\xc2#\xdc\xdd=\x0e\xfa\x0bC\xa9E\x9eeM\x94\x85\x16\xdc\xbd\x8b7\x0fP\xfb\xec\xfb\x8bA\x1dH\x05\x1a@\x85\x00\xce\x85Y\x1eQe%\xdb$\x06T\x11\xf6\xa8\x8fC\xde\x90\xfa\x9c\x16|.oZ\xf4;\xc8Ne\xe5\xa4\xbb\x17K\xc8:\x19\xb6\x96_\xf1\x0fGk\x1b\x15\x1a\xe1T9\xa9\x85\xf39\x16\xab\xc6\x82+\x0b\xb1@\xf4\xaa\xe5"\xff\xae\xa2)\x98z\x10\xd0\x1b\xee\xc8&\xc3\xb9\xa1\x89\xfe\x02\xaa\x82h\x05\x81\xb7\x8f=\xf0\xeaM?\x93\xca\x8e\xa3_\xfc\x90\xf1_}\xb9\x01\x7f\x92\xfa\xfd\x93\x80\xd9\xba27\x97<\xf41<\xf6&\xfc@\xe3\x0eP\xe3X\x8b\xd0G\xb3\x9fG\x8bY28h\xcdP\xc7\xabT5]\x82E\xbf\x0f\x19\x88\xd3u(\xf9\xbb\xfch\x11\x0c\xf9\x17\xde\xbb\xdb\xf1\xf4\xbd\xd0,\xdc\xcc\xdc2i\xfd\xf1\x8alr~\xe5Ki4\xd8@\xe49\x18\xdd\x1e\xc6\x125P\xec7\xa5\x13\xe7+4\xb2\xc2\xa3\xba\xa5\x10\xde\xc3\x03|\xbe\xf2\xfa\x9fn\xd1\xe7\xcc\xd1\xf3\xf6\xe1\x9dL\xe2\xc0\x91\x9a\xf5RI\xa9p\xc2hR\x17\xf7ZU\x89\xcf\x9eT\xdf\xf8D\x9a\xf1U!\x02\t\xe7\xfdA\xdf\xb5\xc2\xf8\xdcr\xeb05\x8a\xc1\x00\xea\x8cr\xda\x18\x84{\xef\xe0n\xad\xe6\x8c\xeb\xfc\xb9!\x03\'\xda\x12\xb5\xc4\x02\x00\xe9\xf6UiGk\xbf\xf2!\x8d\xa4\xf3%H\xffC\xb68~\xc1Aj#\x1e\xe8!\x03O\xf5\xce\xea\xc4\x1a\xcf"\xcd^\xd2\xda\x17\xa6\xdfM\xd85\x8f\xcb+\xfb\x1aC \x8a\xd0\xfe\xaa\xb2tk!\x02l\xe3[)\x14z\xd0\x9eJ\xfeN\xc4\xa71\x90\x95\xf0\x81\x98\xfa\x8b\xab\xbe<V\xe9p\xb1CR\x8d"!\x03\x8d\xdd\xc0l\xe6\x87gzS\xd5O\tm%\x91\xba#\x02\x06\x8c\xf1#\xc1\xf2\xd7\\-\xdd\xc5BUy!\x03\x9d\xaf\xd8W\x1ad\x10X\xcc\xc82\xc5\xe2\x11\x1e\xa3\x9b\t\xc0\xbd\xe3`P\x91C\x84\xf7\xa4\x8b\xce\x9b\xf9!\x02\xd0+\x18s\xa0\x86<\xd0B\xccq}\xa3\x1c\xea\r|\xf9\xdb2\xb7MLr\xc0\x1b\x00\x11P>."W\xae\x01\x00\x00\x95\xdf\x82\xb0\x00\x00\x00\x00'
    rb_hash = b'922ba0c0d06afbeec4c50b0541a29153feaa46c5d7304e7bf7f40870d9f3aeb0'
    rb_prev = b'd14f7359d0ac680b7043720696b14631fc413bc5713029aa620208f081f6deb7'
    rb_merlke = b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
    rb_ts = 1501455939
    rb_h = 343892
    rb_nonce = int.from_bytes(binascii.unhexlify(b'5f4c322eb082df95'), 'big')
    rconsenusdata = 6866918707944415125

    rblock_tx_id = b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
    rblock_tx_nonce = 2961366933
    rblock_inputs = []
    rblock_outputs = []

    # raw block 2 ( block #1)
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
        block = Helper.AsSerializableWithType(BlocksTestCase.b2raw, 'neo.Core.Block.Block')
        return block

    def test_block_deserialize(self):

        block = Helper.AsSerializableWithType(self.rawblock_hex, 'neo.Core.Block.Block')

        self.assertEqual(self.rb_prev, block.PrevHash.ToBytes())
        self.assertEqual(self.rb_merlke, block.MerkleRoot.ToBytes())
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
        out = block.Hash.ToBytes()
        self.assertEqual(out, self.rb_hash)

        root = MerkleTree.ComputeRoot([tx.Hash for tx in block.Transactions])
        self.assertEqual(root, block.MerkleRoot)

    def test_block_two(self):

        hexdata = binascii.unhexlify(self.b2raw)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')
        self.assertEqual(block.Index, self.b2height)
        self.assertEqual(block.ConsensusData, self.b2nonce)
        self.assertEqual(block.Timestamp, self.b2timestamp)
        self.assertEqual(block.PrevHash.ToBytes(), self.b2prev_hash)

        self.assertEqual(block.Hash.ToString(), self.b2hash)

        next_consensus_address = Crypto.ToAddress(block.NextConsensus)

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

        txhash = tx.Hash.ToBytes()
        self.assertEqual(txhash, self.b2tx_id)

        root = MerkleTree.ComputeRoot([tx.Hash for tx in block.Transactions])
        self.assertEqual(root, block.MerkleRoot)

    sf_hash = b'6bfcdff84a3341d7a9299b358f098504e14c99c6774ebaa5dfd631371155533c'
    sf_raw = b'00000000cf9d9c77df2a27eabeaac0b69c282017c328c2da3ec9fbd2ca45b18fdb8cb68a9b6c99d55ac0358b114add3c399357412e9f9878213660dd9daa984332d0e507c5c412594a0000000b5a4046e108122cf3812db982f3b0089a21a278988efeec6a027b2501fd4501405bd82ea1d16a0855c112735a43d83161669b209b1d2d34a2b5c9f744021742ca5671fee68ce62cbe3df2cc231d6ea639fe3d47b70b36b22c8f445b8475069a69405cf8636e0f4e9c4b9e938271e13b020cddd51456c5cb3365a8a052aa03ca5a3cc822e7692907f4b4835b0e237d5cd2a66bda5a1e8d127aa80054de775a1e9ebe408013053b4260eabd2ef03ceed72886d60ae756a25c6cbc5e1dccbbbee3ccd8e6e6f139b9b7d8c7361493eb8706bd9d5ad14c7dbbe89b3a2c4be5a8b68f1592f0405df68939bcf0b218b5a67e9f57c00145ade69fd5f54a6fd5221fb5a8e183b611a4569c642ac5c266b2bacea0e7d89725348e2a2c424a95a1fa5007f03a28346940b3d5c4c7b967ff7f975295f38ffe18a7d2d6f376fd7266aecef690333a6569e6f1e492cde85cb49d4b45b31488663ea7850404186afbc108aceb9c0c7862c43ef155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae0200000b5a404600000000800000014a4dfb91023b1b2086029e03af739d9ceab35fffa8d528de9a6fee3e62bbecbd0000019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50000c16ff286230067f97110a66136d38badc7b9f88eab013027ce4901fd04014099546819767644bbef323e428aab48c8801e66b8c7fb452dcd11205c13f5b198c9b37e9aa6808d6c3a74e50931d3413115e2a86a4a4a99fcae894219c092ca6340a0de35bc6c04c25b8f6cca46b91a35144db40fc94967293500f08c58df81f7c9ecb59cc13bcaca4d932e27a8d9a8204f48d488b6ccdfccd830c22bf4b7353dd64039346418372b541dfe7fdc99611bfc59cee881044da2912cb2404b885c6472310a2b771153e6a0022abb11aa41288ef98a2aed1bb42714fa6a1c6e85e415b8bb4045cc681dbe07155b554b0291f0352546223e49e3192c221249c29eb97651aec3c5f2f6adfc85a87cfdfef3a15d57391cf99190e8d80b01fcc1ebf8f48c745957f154210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae'
    sf_merk = b'07e5d0324398aa9ddd60362178989f2e415793393cdd4a118b35c05ad5996c9b'
    sf_txlen = 2
    sf_tx1_id = b'f2195b0382fca1d8648fe0f9bdbf441ac4f651f614bfbf5d92ba842a9698e9f1'
    sf_tx2_id = b'4feb0081f9425cab84269127bef0a871a84d4408f09923d17ebb257cd231b362'
    sf2_vin_len = 1
    sf2_vo_len = 1

    def test_block_seventyfour(self):

        hexdata = binascii.unhexlify(self.sf_raw)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.MerkleRoot.ToBytes(), self.sf_merk)
        self.assertEqual(block.Hash.ToBytes(), self.sf_hash)

    pb_raw = b'00000000f7f81039bc589a1fcf89e77944a7434da7660bd1ca1584a4cc7f1983548050d1dc937c5a3f1081828080c4ac279e804295f54525d10739ad34b53caf3da8822d83d11259e800000092abe1e9ff2a383af3812db982f3b0089a21a278988efeec6a027b2501fd45014069af682cb67a122d26c073cce731efd0386d200f56505e611539ae30cee65a6f7b7275dc1bb9080f3420b34b8adf3d770b3f6e15eaa79aeba2fe3c1603b8242340faa17d6e37a2b71f0ec51188c88c6962b113646bc7f122d4f4da4564a483631e4d8cc58340f396f41bbc4f209c1eec34cd62f099817386718602c5aa5acc2c4b407c006dbaaa100a2b2eee2e7f8c7f602993e4802b83ce3a9638acb437498afc2a55a7c8075cd5d8b8d086d6a379d413358915d66462b9613dee18347cd2f3fe7a4058a553b3b0bde72270aeb74c2026c4183daab5e4f7291a93e45527c775529c97174b664f487433cca8ea46d67f8298ccd209bd355c56747eb5a14ce92295e00b4003e2efc22e39302f8fbf94115c59fd8f17cc553702dc2e7d01b849f7d463fb81639f1d60e7eac1f95a562a04571f37109cde1944010bab8be1f348e97006100af155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae02000092abe1e900000000d000fd3f01746b4c04000000004c04000000004c040000000061681e416e745368617265732e426c6f636b636861696e2e476574486569676874681d416e745368617265732e426c6f636b636861696e2e476574426c6f636b744c0400000000948c6c766b947275744c0402000000936c766b9479744c0400000000948c6c766b9479681d416e745368617265732e4865616465722e47657454696d657374616d70a0744c0401000000948c6c766b947275744c0401000000948c6c766b9479641b004c0400000000744c0402000000948c6c766b947275623000744c0401000000936c766b9479744c0400000000936c766b9479ac744c0402000000948c6c766b947275620300744c0402000000948c6c766b947961748c6c766b946d748c6c766b946d748c6c766b946d746c768c6b946d746c768c6b946d746c768c6b946d6c75660302050001044c6f636b0c312e302d70726576696577310a4572696b205a68616e67126572696b40616e747368617265732e6f7267234c6f636b20796f75722061737365747320756e74696c20612074696d657374616d702e00014e23ac4c4851f93407d4c59e1673171f39859db9e7cac72540cd3cc1ae0cca87000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000ebcaaa0d00000067f97110a66136d38badc7b9f88eab013027ce49014140c298da9f06d5687a0bb87ea3bba188b7dcc91b9667ea5cb71f6fdefe388f42611df29be9b2d6288655b9f2188f46796886afc3b37d8b817599365d9e161ecfb62321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    pb_hash = b'077c7fc9a85d777aeb42e1076bd98451f16e59354bfb6fed998ccabd93f6ccb9'

    def test_block_publish_tx(self):

        hexdata = binascii.unhexlify(self.pb_raw)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.Hash.ToBytes(), self.pb_hash)

    t992 = b'000000001db78fc59944ef5a8c865efc09b244896e8f32253fb21fb47e13128706cae385b9c95339d1fa2ea86bcdb3e79d05a5b42c35789dff5c54027d24fa549a66684c3f9b1359b00b000066666542ed4bbc15f3812db982f3b0089a21a278988efeec6a027b2501fd4501400bfee22cb2e369debb4fe5c52bcc33c17b25aa9402aa915e3db82fd41e711966d15e255434b4a99622a831ba0fc6cc99f288a2605818cd4bc0b807a05ffe1c9740e16607602ca56dec01c17d3ad1ffa9b425bc38bd7a4bca7348fed11b867bdf16cb9d571bab51f56d7e8c8114f6a01d4e0c107ea99dd5e23a4ae488cbd26d17c340d3771b97e559fc116680ff7cf4e9aa36826a40d8cd3c59a578d45078fbcac9f1b98f125acb7de9235ff1087c1efde2ecfc2b82e95ec98769adb39ee88da9745740caced10c3b24ad134da0561396abfa4d94c3847226214c9ff451b593b0d3959e2ea6abe3afd9bbce1f7d3cd9ab61b80dd5afd81dbc987a488160f9dafaacd8b2408038ce11fa724bba34987ff001fba349735273a3b7a580828c3b762b837b958100fc65acae1598b23b32303d10ec99ee2421cbc5838a7e261d8e3accbef7ff5ef155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae0100006666654200000000'
    t992h = b'bcfc016b33f6abc1f1109878f6d69a8aaf42b9ac09c5793507afbbdccdb8f68f'
    t992m = b'4c68669a54fa247d02545cff9d78352cb4a5059de7b3cd6ba82efad13953c9b9'

    def test_2992(self):

        hexdata = binascii.unhexlify(self.t992)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')
        self.assertEqual(block.MerkleRoot.ToBytes(), self.t992m)
        self.assertEqual(block.Hash.ToBytes(), self.t992h)

        json = block.ToJson()
        self.assertEqual(json['index'], 2992)
        self.assertEqual(json['hash'], '0x%s' % self.t992h.decode('utf-8'))
        self.assertEqual(json['merkleroot'], '0x%s' % self.t992m.decode('utf-8'))
        self.assertEqual(len(json['tx']), 1)
        self.assertEqual(json['tx'][0]['txid'], '0x4c68669a54fa247d02545cff9d78352cb4a5059de7b3cd6ba82efad13953c9b9')

    big_tx_hash = b'93fb1184b95fd785022dea163ffc60ef6fa548ca240b49dd8339700cee581991'

    def test_1050514(self):

        path = '%s/fixtures/1050514.txt' % os.getcwd()

        with open(path, 'rb') as f:
            #
            blockraw = f.read().strip()

            hex = binascii.unhexlify(blockraw)

            block = Helper.AsSerializableWithType(hex, 'neo.Core.Block.Block')

            self.assertEqual(self.big_tx_hash, block.Hash.ToBytes())

        json = block.ToJson()

        self.assertEqual(json['index'], 1050514)
        self.assertEqual(json['hash'], '0x%s' % self.big_tx_hash.decode('utf-8'))
        self.assertEqual(len(json['tx']), 65)

        for tx in json['tx']:
            if tx['txid'] == '1dc3543a5b54fcfce3fefba6c772f3a59740b2b1784690b3c66e2f7052f002bb':
                bigclaim = tx
                self.assertEqual(len(bigclaim['claims']), 1756)
                vout = bigclaim['vout'][0]
                self.assertEqual(vout['ScriptHash'], 'AFnRHRQceaUgFQxPTttAQzAZvsjGSNtHCH')
                self.assertEqual(vout['Value'], 5786800133972)

    b_1321456_merlke = '7020347797526cea93a0cd47303e3274afe6f79dd0d184a0e55cc673fdd1d382'

    b_132156_txids = [
        'a4b0def576397d4b66b5911888867dcee0fe67833f35c9c6d9ad12af34b25190',
        '1cd3060b7f75addd9bbd078c7eb0483a8b6c05b5a932f3d487674ff17404a81f',
        '9a299703b27187a6a9157cbb90bf372421aab0e0786e50eb4c292ecd0171ef06',
        '61e4af6da434c708865bec387e60cb09476871a92ea2a3716d78cf34eda16f6e',
        '167c5a3905d6f3495f41fef9094e97fe42ce2ba608cffd4a74324d8242de5589',
        'bc21700872ae2ed27983ad64e485e069b6e9d341aca3bfcb18ee953b77aaebe3',
        'bdf3f4357cf5bca685607f405abb1ec2202b699da0a1db16911302205b402fe3',
        'cccadeee3df2c4d70a4b8563b374bb3c4eb60c850999f81fec5ee56149814249',
        '3c6c8c77f05f9e0da53a072e694eec498a3894f683cbf59f70625780c31f55c3',
        '8d95ac8a60bc004baa779a9e9da2f465c13108505c70daad95a9c977228dbf46',
        '170cfd5e0ce4162937f2e4c4331de7bb3a1cb342fb3e7167ed16fbbd8020b791',
        '50e404d8850545fe773e82af93a1b84643cc6403d44f882f7f7b2eb23e42fc60',
        '14ff62cb005ba8697e8300877a1c6c1ca8f89c8460f747e9a79bede69f8fb65b',
        '3ac733706d44c8409569014f8b1cdcb01e001bc1b1c56551197591559fe20af0',
        '9af1fcaab6fec80922e25dbea34c534c743dcf8d10f76af1892526c2879d3a70',
    ]

    def test_1321456(self):

        path = '%s/fixtures/1321456.txt' % os.getcwd()

        with open(path, 'rb') as f:

            blockraw = f.read().strip()

            hex = binascii.unhexlify(blockraw)

            block = Helper.AsSerializableWithType(hex, 'neo.Core.Block.Block')

            for tx in block.Transactions:

                hash = tx.Hash.ToString()

                self.assertTrue(hash in self.b_132156_txids)

            self.assertEqual(block.MerkleRoot.ToString(), self.b_1321456_merlke)

    def test_testnet797966(self):

        path = '%s/fixtures/797966.txt' % os.getcwd()

        with open(path, 'rb') as f:

            blockraw = f.read().strip()

            hex = binascii.unhexlify(blockraw)

            block = Helper.AsSerializableWithType(hex, 'neo.Core.Block.Block')

            trimmed = block.Trim()

            trimmed_unhex = binascii.unhexlify(trimmed)

            blockfrom_trimmed = Block.FromTrimmedData(trimmed_unhex, 0)

            self.assertEqual(blockfrom_trimmed.Version, block.Version)
            self.assertEqual(blockfrom_trimmed.Index, block.Index)
            self.assertEqual(blockfrom_trimmed.PrevHash, block.PrevHash)
            self.assertEqual(blockfrom_trimmed.MerkleRoot, block.MerkleRoot)
            self.assertEqual(blockfrom_trimmed.Timestamp, block.Timestamp)
            self.assertEqual(blockfrom_trimmed.Index, block.Index)
            self.assertEqual(blockfrom_trimmed.ConsensusData, block.ConsensusData)
            self.assertEqual(blockfrom_trimmed.NextConsensus, block.NextConsensus)
            self.assertEqual(len(block.Transactions), len(blockfrom_trimmed.Transactions))

    block_bytes = b'\x00\x00\x00\x00\xed\x00.\xa6\xc6(\xa2\x80\x1a\x95E\x8f\xb4\xaa\xcc$\x98\x031\xd3\xca2!-\x1a\xaa/m!\xb8V\xa4Jj\xd4\xad6\xc1a\xb25-5\xe5\xd7\xec\xe2\x13T\xbb\xf6\x02\xa4\xaes\x98((\xd7i\n\x81\xfa\xf6\xf0neZ\\\xe6\x0f\x00\x88\xb7\xcf\xab\xb3d\x88M\xf3\x81-\xb9\x82\xf3\xb0\x08\x9a!\xa2x\x98\x8e\xfe\xecj\x02{%\x01\xfdE\x01@\xa0Z\xf8\xda\x93*\xd0\x04\xdcq\x06\xd5\x86\x07G\xd0 \\;\xb3cg\xcc\xf3=}B\x07\xf4\'\xf1k\xe4\x80|\xb9\x07\x9e\xa8\x8b\x9f\xf0\xd7 \xbb\x1a\x82\xa1\xa5\x9a\xb0\x9e\xf4\x1a\xb7\x89S\xd4\xeai\x8f\x8b\xcb_@x\x8a%\x07\x93\x14\x04\xbc\r\x9d\xdb\xc2A\xc0\x8d\x07\x13F\xd1An\xf8$\x02\xa0\xe4\n1?I\x9a\xfc.\xf0e\x8c\xda\x9dv\xc3\xac\xd7\xdav\x91:V\xba\xb2pK\xceF\xc4Z\xc6boj\xdc\x1e\xc3\xd4\x06@\xd9\x8cH\xa7\xa5*\xba\xb9\xac~\xf8\x05\xecONc\xb0\xa5\x1aH0\xfd\x11K>pL\x84\xd9\xaeK,\x87\x92x5d\xc1\xa7m\x1f!)\x9fl\xa5\x12>\x07md\x83\x17#\x1f"\xb9Uk\x82\xaf\xfb\xaa\xbb@n\x8b\x1a\x96\x85O\xf2\x84-\xeb\xa3d\xe4\xad\x9e":\xbc\xab5\xe6$P\xef\x91\xe3\xc3\xaf\x11\xc2f\xde\xf6\xec\xc55k\xe7\xdf\x9a?Z2v\xedF4\x01p)5\r\xd2t+\x10Y\xe2\x8a\x05I:\x13I@\xc3H\xb3/\x06\x08\xcb\xcf\xd1\xa5\xd8\xa6,3m1\x909\x1b\x17\xda^\xea\xee\xcc\x1e\x02\x90h\xb0\x04\x1a\x94\x92~o\xf2^\x0e\xca\x821\xb90\t\x98\xd2\xad\xc8\xdc\xb5<\xa4\x99\xc2c\xe9\xb9\x91\x7fS\xa0=\t\xf1U!\x02\t\xe7\xfdA\xdf\xb5\xc2\xf8\xdcr\xeb05\x8a\xc1\x00\xea\x8cr\xda\x18\x84{\xef\xe0n\xad\xe6\x8c\xeb\xfc\xb9!\x03\'\xda\x12\xb5\xc4\x02\x00\xe9\xf6UiGk\xbf\xf2!\x8d\xa4\xf3%H\xffC\xb68~\xc1Aj#\x1e\xe8!\x03O\xf5\xce\xea\xc4\x1a\xcf"\xcd^\xd2\xda\x17\xa6\xdfM\xd85\x8f\xcb+\xfb\x1aC \x8a\xd0\xfe\xaa\xb2tk!\x02l\xe3[)\x14z\xd0\x9eJ\xfeN\xc4\xa71\x90\x95\xf0\x81\x98\xfa\x8b\xab\xbe<V\xe9p\xb1CR\x8d"!\x03\x8d\xdd\xc0l\xe6\x87gzS\xd5O\tm%\x91\xba#\x02\x06\x8c\xf1#\xc1\xf2\xd7\\-\xdd\xc5BUy!\x03\x9d\xaf\xd8W\x1ad\x10X\xcc\xc82\xc5\xe2\x11\x1e\xa3\x9b\t\xc0\xbd\xe3`P\x91C\x84\xf7\xa4\x8b\xce\x9b\xf9!\x02\xd0+\x18s\xa0\x86<\xd0B\xccq}\xa3\x1c\xea\r|\xf9\xdb2\xb7MLr\xc0\x1b\x00\x11P>."W\xae\x02\x00\x00\x88\xb7\xcf\xab\x00\x00\x00\x00\x90\x00\x01H!\x03\xc0\x89\xd7\x12+\x84\nI5#N\x82\xe2j\xe5\xef\xd0\xc2\xac\xb6\'#\x9d\xc9\xf2\x071\x137\xb6\xf2\xc1\nRegistered\x01\x01\x00\x01\xcbA\x84\xf0\xa9nrel\x1f\xbd\xd4\xf7\\\xcaVu\x19\xe9\t\xfdC\xce\xfc\xec\x13\xd6\xc6\xab\xcb\x92\xa1\x00\x00\x01\xe7-(iy\xeel\xb1\xb7\xe6]\xfd\xdf\xb2\xe3\x84\x10\x0b\x8d\x14\x8ewX\xdeB\xe4\x16\x8bqy,`\x00\xb8\xfb\x05\x01\t\x00\x00q\xf9\xcf\x7f\x0e\xc7N\xc0\xb0\xf2\x8a\x92\xb1.\x10\x81WL\n\xf0\x01A@\x87\x80\xd7\xb3\xc0\xaa\xdcS\x98\x15=\xf5\xe2\xf1\xcf\x15\x9d\xb2\x1b\x8b\x0f4\xd3\x99M\x86T3\xf7\x9f\xaf\xacAh7\x83\xc4\x8a\xefQ\x0bgf\x0e1W\xb7\x01\xb9\xcaM\xd9\x94j8]W\x8f\xba}\xd2oHI#!\x03\xc0\x89\xd7\x12+\x84\nI5#N\x82\xe2j\xe5\xef\xd0\xc2\xac\xb6\'#\x9d\xc9\xf2\x071\x137\xb6\xf2\xc1\xac'

    def test_testnet10412011(self):

        block = Helper.AsSerializableWithType(self.block_bytes, 'neo.Core.Block.Block')
        self.assertEqual(len(block.Transactions), 2)
        state_tx = block.Transactions[1]
        self.assertIsInstance(state_tx, StateTransaction)
        self.assertEqual(len(state_tx.Descriptors), 1)
        descriptor = state_tx.Descriptors[0]
        self.assertIsInstance(descriptor, StateDescriptor)
        self.assertEqual(descriptor.Type, StateType.Validator)
        self.assertEqual(descriptor.SystemFee, Fixed8.FromDecimal(1000))
        self.assertEqual(descriptor.Key, binascii.unhexlify(b'03c089d7122b840a4935234e82e26ae5efd0c2acb627239dc9f207311337b6f2c1'))
