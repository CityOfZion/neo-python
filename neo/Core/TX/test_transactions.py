from neo.Utils.NeoTestCase import NeoTestCase
from neo.Core.Helper import Helper
from neo.Core.Size import GetVarSize
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.State.AssetState import AssetState
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.Core.IO.BinaryReader import BinaryReader
from neo.IO.Helper import Helper as IOHelper
from neo.Core.Fixed8 import Fixed8
from neo.IO.MemoryStream import MemoryStream, StreamManager
import binascii
import os
from neo.Settings import settings
from mock import patch
from neo.Blockchain import GetBlockchain


class TransactionTestCase(NeoTestCase):

    def test_tx_types(self):
        self.assertEqual('ContractTransaction', TransactionType.ToName(TransactionType.ContractTransaction))
        self.assertEqual('MinerTransaction', TransactionType.ToName(0))
        self.assertEqual('StateTransaction', TransactionType.ToName(b'\x90'))
        self.assertEqual(None, TransactionType.ToName(123))

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

        self.assertEqual(type(tx), MinerTransaction)

        self.assertEqual(tx.Hash.ToBytes(), self.tx_id)

        self.assertEqual(tx.Nonce, self.tx_nonce)

        self.assertEqual(tx.inputs, [])
        self.assertEqual(tx.outputs, [])
        self.assertEqual(tx.scripts, [])

        ms = MemoryStream()
        writer = BinaryWriter(ms)

        tx.Serialize(writer)
        out = ms.ToArray()

        self.assertEqual(out, self.tx_raw)

        json = tx.ToJson()
        self.assertEqual(json['nonce'], self.tx_nonce)

    ctx_raw = b'800000014a4dfb91023b1b2086029e03af739d9ceab35fffa8d528de9a6fee3e62bbecbd0000019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50000c16ff286230067f97110a66136d38badc7b9f88eab013027ce4901fd04014099546819767644bbef323e428aab48c8801e66b8c7fb452dcd11205c13f5b198c9b37e9aa6808d6c3a74e50931d3413115e2a86a4a4a99fcae894219c092ca6340a0de35bc6c04c25b8f6cca46b91a35144db40fc94967293500f08c58df81f7c9ecb59cc13bcaca4d932e27a8d9a8204f48d488b6ccdfccd830c22bf4b7353dd64039346418372b541dfe7fdc99611bfc59cee881044da2912cb2404b885c6472310a2b771153e6a0022abb11aa41288ef98a2aed1bb42714fa6a1c6e85e415b8bb4045cc681dbe07155b554b0291f0352546223e49e3192c221249c29eb97651aec3c5f2f6adfc85a87cfdfef3a15d57391cf99190e8d80b01fcc1ebf8f48c745957f154210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae'
    ctx_id = b'4feb0081f9425cab84269127bef0a871a84d4408f09923d17ebb257cd231b362'  # see https://neoscan-testnet.io/transaction/4FEB0081F9425CAB84269127BEF0A871A84D4408F09923D17EBB257CD231B362

    def test_contract_tx_deserialize(self):
        ms = MemoryStream(binascii.unhexlify(self.ctx_raw))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.ctx_raw)
        self.assertEqual(tx.Hash.ToBytes(), self.ctx_id)

        json = tx.ToJson()
        self.assertEqual(json['size'], 605)
        self.assertEqual(json['type'], 'ContractTransaction')

    pb_raw = b'd000fd3f01746b4c04000000004c04000000004c040000000061681e416e745368617265732e426c6f636b636861696e2e476574486569676874681d416e745368617265732e426c6f636b636861696e2e476574426c6f636b744c0400000000948c6c766b947275744c0402000000936c766b9479744c0400000000948c6c766b9479681d416e745368617265732e4865616465722e47657454696d657374616d70a0744c0401000000948c6c766b947275744c0401000000948c6c766b9479641b004c0400000000744c0402000000948c6c766b947275623000744c0401000000936c766b9479744c0400000000936c766b9479ac744c0402000000948c6c766b947275620300744c0402000000948c6c766b947961748c6c766b946d748c6c766b946d748c6c766b946d746c768c6b946d746c768c6b946d746c768c6b946d6c75660302050001044c6f636b0c312e302d70726576696577310a4572696b205a68616e67126572696b40616e747368617265732e6f7267234c6f636b20796f75722061737365747320756e74696c20612074696d657374616d702e00014e23ac4c4851f93407d4c59e1673171f39859db9e7cac72540cd3cc1ae0cca87000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000ebcaaa0d00000067f97110a66136d38badc7b9f88eab013027ce49014140c298da9f06d5687a0bb87ea3bba188b7dcc91b9667ea5cb71f6fdefe388f42611df29be9b2d6288655b9f2188f46796886afc3b37d8b817599365d9e161ecfb62321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    pb_hash = b'5467a1fc8723ceffa8e5ee59399b02eea1df6fbaa53768c6704b90b960d223fa'  # see https://neoscan-testnet.io/transaction/5467A1FC8723CEFFA8E5EE59399B02EEA1DF6FBAA53768C6704B90B960D223FA

    def test_publish_tx_deserialize(self):
        ms = MemoryStream(binascii.unhexlify(self.pb_raw))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.pb_raw)
        self.assertEqual(tx.Hash.ToBytes(), self.pb_hash)

        json = tx.ToJson()
        self.assertEqual(json['size'], 613)
        self.assertEqual(json['type'], 'PublishTransaction')

        contract = json['contract']
        self.assertEqual(contract['author'], 'Erik Zhang')
        self.assertEqual(contract['description'], 'Lock your assets until a timestamp.')

        self.assertEqual(contract['code']['hash'], '0xffbd1a7ad1e2348b6b3822426f364bfb4bcce3b9')
        self.assertEqual(contract['code']['returntype'], "Boolean")
        self.assertEqual(contract['code']['parameters'], ['Integer', 'ByteArray', 'Signature'])
        self.assertEqual(Fixed8.FromDecimal(settings.ALL_FEES['PublishTransaction']), tx.SystemFee())

    ir = b'd100644011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111081234567890abcdef0415cd5b0769cc4ee2f1c9f4e0782756dabf246d0a4fe60a035400000000'
    ir_id = b'1a328cdd53c7f1710b4006304e8c75236a9b18523f037cdf069a96f0d7f01379'  # see https://neoscan-testnet.io/transaction/1A328CDD53C7F1710B4006304E8C75236A9B18523F037CDF069A96F0D7F01379

    def test_invocation_transaction(self):
        ms = MemoryStream(binascii.unhexlify(self.ir))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.ir)
        self.assertEqual(tx.Hash.ToBytes(), self.ir_id)

        json = tx.ToJson()
        self.assertEqual(json['size'], 107)
        self.assertEqual(json['type'], "InvocationTransaction")

    mr = b'00006666654200000000'
    mrn = 1113941606
    mrh = b'4c68669a54fa247d02545cff9d78352cb4a5059de7b3cd6ba82efad13953c9b9'

    def test_miner_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.mr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.Nonce, self.mrn)
        self.assertEqual(tx.ToArray(), self.mr)
        self.assertEqual(tx.Hash.ToBytes(), self.mrh)

    def test_check_miner_tx_size(self):
        """ see original test here
            https://github.com/neo-project/neo/blob/5ce0e4c3192cdcce700105030ed03197961e0466/neo.UnitTests/UT_MinerTransaction.cs#L39-L48
        """
        m_tx = MinerTransaction()
        self.assertEqual(m_tx.Size(), 10)

    rr = b'400060245b7b226c616e67223a227a682d434e222c226e616d65223a2254657374436f696e227d5dffffffffffffffff08034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e1167f97110a66136d38badc7b9f88eab013027ce4900014423a26aeca49cdeeb9522c720e1ae3a93bbe27d53662839b16a438305c20906010001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60001e1a210b00000067f97110a66136d38badc7b9f88eab013027ce490141405d8223ec807e3416a220a75ef9805dfa2e36bd4f6dcc7372373aa45f15c7fadfc96a8642e52acf56c2c66d549be4ba820484873d5cada00b9c1ce9674fbf96382321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    rrid = b'0c092117b4ba47b81001712425e6e7f760a637695eaf23741ba335925b195ecd'  # see https://neoscan-testnet.io/transaction/0C092117B4BA47B81001712425E6E7F760A637695EAF23741BA335925B195ECD

    def test_register_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.rr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(self.rrid, tx.Hash.ToBytes())

        json = tx.ToJson()
        asset = json['asset']

        self.assertEqual(asset['admin'], 'ARFe4mTKRTETerRoMsyzBXoPt2EKBvBXFX')
        self.assertEqual(asset['name'], b'[{"lang":"zh-CN","name":"TestCoin"}]')
        self.assertEqual(asset['precision'], 8)
        self.assertEqual(Fixed8.FromDecimal(settings.ALL_FEES['RegisterTransaction']), tx.SystemFee())
        self.assertEqual(json['size'], 302)

    ii = b'01000000019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50000c16ff28623005fa99d93303775fe50ca119c327759313eccfa1c01000151'
    ii_id = b'3631f66024ca6f5b033d7e0809eb993443374830025af904fb51b0334f127cda'  # see https://neoscan.io/transaction/3631f66024ca6f5b033d7e0809eb993443374830025af904fb51b0334f127cda

    def test_issue_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.ii))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(self.ii_id, tx.Hash.ToBytes())

        json = tx.ToJson()
        self.assertEqual(json['size'], 69)
        self.assertEqual(json['type'], "IssueTransaction")
        self.assertEqual(json['version'], 0)
        self.assertEqual(len(json['attributes']), 0)

        jsn_vout = json['vout'][0]
        self.assertEqual(jsn_vout['asset'], "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b")
        self.assertEqual(jsn_vout['value'], "100000000")
        self.assertEqual(jsn_vout['address'], "AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i")

        self.assertEqual(len(json['vin']), 0)
        self.assertEqual(json['sys_fee'], "0")
        self.assertEqual(json['net_fee'], "0")
        self.assertEqual(json['scripts'][0]['invocation'], "")
        self.assertEqual(json['scripts'][0]['verification'], "51")

    cr = b'800001f012e99481e4bb93e59088e7baa6e6b58be8af9502f8e0bc69b6af579e69a56d3d3d559759cdb848cb55b54531afc6e3322c85badf08002c82c09c5b49d10cd776c8679789ba98d0b0236f0db4dc67695a1eb920a646b9000001cd5e195b9235a31b7423af5e6937a660f7e7e62524710110b847bab41721090c0061c2540cd1220067f97110a66136d38badc7b9f88eab013027ce490241400bd2e921cee90c8de1a192e61e33eb8980a3dc00c388ee9aac0712178cc8fceed8bb59788f7caf3c4dc082abcdaaa49772fda86db4ceea243bda31bcde9b8a0b3c21034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e1104182f145967cc4ee2f1c9f4e0782756dabf246d0a4fe60a035441402fe3e20c303e26c3817fed6fc7db8edde4ac62b16eee796c01c2b59e382b7ddfc82f0b36c7f7520821c7b72b9aff50ae27a016961f1ef1dade9cafa85655380f2321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    cr2 = b'800001f012e99481e4bb93e59088e7baa6e6b58be8af9502f8e0bc69b6af579e69a56d3d3d559759cdb848cb55b54531afc6e3322c85badf08002c82c09c5b49d10cd776c8679789ba98d0b0236f0db4dc67695a1eb920a646b9000001cd5e195b9235a31b7423af5e6937a660f7e7e62524710110b847bab41721090c0061c2540cd1220067f97110a66136d38badc7b9f88eab013027ce49'
    crid = b'e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff178'  # see https://neoscan-testnet.io/transaction/E4D2EA5DF2ADF77DF91049BECCBB16F98863B93A16439C60381EAC1F23BFF178

    def test_contract_tx_again(self):
        ms = MemoryStream(binascii.unhexlify(self.cr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.cr)
        self.assertEqual(tx.Hash.ToBytes(), self.crid)

    p2 = b'd000a9746b7400936c766b94797451936c766b9479a1633a007400936c766b94797451936c766b94797452936c766b9479617c6554009561746c768c6b946d746c768c6b946d746c768c6b946d6c75667400936c766b94797451936c766b9479617c6525007452936c766b94799561746c768c6b946d746c768c6b946d746c768c6b946d6c7566746b7400936c766b94797451936c766b94799361746c768c6b946d746c768c6b946d6c756600ff09e5919ce5919ce5919c04302e3031037777770377777704656565660001fb9b53e0a87295a94973cd395d64c068c705d662e3965682b2cb36bf67acf7e5000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60001edc0c1700000050ac4949596f5b62fef7be4d1c3e494e6048ed4a0141402725b8f7e5ada56e5c5e85177cdda9dd6cf738a7f35861fb3413c4e05017125acae5d978cd9e89bda7ab13eb87ba960023cb44d085b9d2b06a88e47cefd6e224232102ff8ac54687f36bbc31a91b730cc385da8af0b581f2d59d82b5cfef824fd271f6ac'
    p22 = b'd000a9746b7400936c766b94797451936c766b9479a1633a007400936c766b94797451936c766b94797452936c766b9479617c6554009561746c768c6b946d746c768c6b946d746c768c6b946d6c75667400936c766b94797451936c766b9479617c6525007452936c766b94799561746c768c6b946d746c768c6b946d746c768c6b946d6c7566746b7400936c766b94797451936c766b94799361746c768c6b946d746c768c6b946d6c756600ff0ae5919ce5919ce5919c05302e3031047777770477777705656565660001fb9b53e0a87295a94973cd395d64c068c705d662e3965682b2cb36bf67acf7e5000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60001edc0c1700000050ac4949596f5b62fef7be4d1c3e494e6048ed4a0141402725b8f7e5ada56e5c5e85177cdda9dd6cf738a7f35861fb3413c4e05017125acae5d978cd9e89bda7ab13eb87ba960023cb44d085b9d2b06a88e47cefd6e224232102ff8ac54687f36bbc31a91b730cc385da8af0b581f2d59d82b5cfef824fd271f6ac'
    p2id = b'514157940a3e31b087891c5e8ed362721f0a7f3dda3f80b7a3fe618d02b7d3d3'  # see https://neoscan-testnet.io/transaction/514157940A3E31B087891C5E8ED362721F0A7F3DDA3F80B7A3FE618D02B7D3D3

    def test_pub_two(self):
        ms = MemoryStream(binascii.unhexlify(self.p2))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.p2)
        self.assertEqual(tx.Hash.ToBytes(), self.p2id)

        json = tx.ToJson()
        self.assertEqual(json['size'], 402)
        self.assertEqual(json['type'], 'PublishTransaction')

    eraw = b'200002ff8ac54687f36bbc31a91b730cc385da8af0b581f2d59d82b5cfef824fd271f60001d3d3b7028d61fea3b7803fda3d7f0a1f7262d38e5e1c8987b0313e0a94574151000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60005441d11600000050ac4949596f5b62fef7be4d1c3e494e6048ed4a01414079d78189d591097b17657a62240c93595e8233dc81157ea2cd477813f09a11fd72845e6bd97c5a3dda125985ea3d5feca387e9933649a9a671a69ab3f6301df6232102ff8ac54687f36bbc31a91b730cc385da8af0b581f2d59d82b5cfef824fd271f6ac'
    eid = b'988832f693785dcbcb8d5a0e9d5d22002adcbfb1eb6bbeebf8c494fff580e147'  # see https://neoscan-testnet.io/transaction/988832F693785DCBCB8D5A0E9D5D22002ADCBFB1EB6BBEEBF8C494FFF580E147

    def test_enrollment_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.eraw))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.eraw)
        self.assertEqual(tx.Hash.ToBytes(), self.eid)
        self.assertEqual(Fixed8.FromDecimal(settings.ALL_FEES['EnrollmentTransaction']), tx.SystemFee())

        json = tx.ToJson()
        self.assertEqual(json['size'], 235)
        self.assertEqual(json['type'], 'EnrollmentTransaction')

    yatx = b'800001f00431313131010206cc6f919695fb55c9605c55127128c29697d791af884c2636416c69a944880100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f50500000000e58e5999bcbf5d78f52ead40654131abb9ee27099b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5009a04f516000000e53a27d37d7f5a3187003c21efe3725304a7410601414058b4a41beabdcf62381f7feea02767a714eb8ea49212fdb47a6f0bed2d0ae87d27377d9c2b4412ebf816042f2144e6e08939c7d83638b61208d3a7f5ea47c3ba232102ca81fa6c7ef20219c417d876c2743ea87728d416632d09c18004652aed09e000ac'
    yatx_id = b'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4'

    def test_yet_another_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.yatx))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.yatx)
        self.assertEqual(tx.Hash.ToBytes(), self.yatx_id)

    cltx = b'02000c56b979be6f3e719c455dfb5a2744e00f1a8cc4ae854f7ffdf5b461759b5336f7000046281282c739d2d735b12c780b831523e58d9aa9eedbdba8889cb8fb335d5b860100841c245f716451928f1cc13d77f01a7bf732371dd4276ee0686d99b42e0020c00100841c245f716451928f1cc13d77f01a7bf732371dd4276ee0686d99b42e0020c00200841c245f716451928f1cc13d77f01a7bf732371dd4276ee0686d99b42e0020c000007f86e6cab7f055e64bf048db31c19bd5034a0c9db698979e1aa55eb5e468fc9703007f86e6cab7f055e64bf048db31c19bd5034a0c9db698979e1aa55eb5e468fc9702007f86e6cab7f055e64bf048db31c19bd5034a0c9db698979e1aa55eb5e468fc9701007f86e6cab7f055e64bf048db31c19bd5034a0c9db698979e1aa55eb5e468fc97000097ffc5adef75e1b5f1b853e55d982ec5c5ab187c6b22f467306b551815e633b2000097ffc5adef75e1b5f1b853e55d982ec5c5ab187c6b22f467306b551815e633b2010097ffc5adef75e1b5f1b853e55d982ec5c5ab187c6b22f467306b551815e633b20200000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60cb2cd2010000000019ae118ef7951731c342d26bbac954c56e8b35d20141406b74653deba7f80474a9b8230d220a038f2ea98d3f401df44b71560b13af914c28002c4ee977b0fb7e8a65bdccf372db852f0f6ea41978314dd38065ce7874a8232103cfb3ad2685ad402dd5122ab83dc1d6a026e8363c905a2c73668825ad2f922d39ac'
    cltx_id = b'9bf8c14c3ddadf002dc9a4d3a3321623ceb356ce170ee683efe4ac0f0570f81c'  # see https://neoscan-testnet.io/transaction/9bf8c14c3ddadf002dc9a4d3a3321623ceb356ce170ee683efe4ac0f0570f81c

    def test_claim_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.cltx))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.cltx)
        self.assertEqual(tx.Hash.ToBytes(), self.cltx_id)

        json = tx.ToJson()
        self.assertEqual(json['size'], 577)
        self.assertEqual(json['type'], "ClaimTransaction")
        self.assertEqual(json['version'], 0)
        self.assertEqual(len(json['attributes']), 0)
        self.assertEqual(len(json['vout']), 1)
        self.assertEqual(len(json['vin']), 0)
        self.assertEqual(json['sys_fee'], "0")
        self.assertEqual(json['net_fee'], "0")

        self.assertEqual(len(json['claims']), 12)

    sttx = b'9000014821025bdf3f181f53e9696227843950deb72dcd374ded17c057159513c3d0abe20b640a52656769737465726564010100015a8e6d99a868ae249878516ac521441b3f5098221ce15bcdd712efb58dda494900000001414098910b485b34a52340ac3baab13a63695b5ca44538c968ca6f2aa540654e8394ee08cc7a312144f794e780f56510f5f581e1df41859813d4bb3746b02fab15bb2321025bdf3f181f53e9696227843950deb72dcd374ded17c057159513c3d0abe20b64ac'
    sttx_id = b'ccf1404325a601ce7a33291f196bab2c9d4e80581736bfdb5a2325c7aa74427e'  # see https://neoscan.io/transaction/ccf1404325a601ce7a33291f196bab2c9d4e80581736bfdb5a2325c7aa74427e

    def test_state_tx(self):
        ms = MemoryStream(binascii.unhexlify(self.sttx))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        # the net_fee calculation in short is : net_fee = inputs - outputs -system fee.
        # For this test to be able to grab the input values we need to make the TX that it references available for this test
        ms2 = MemoryStream(binascii.unhexlify(
            b'80000001def3ab1c73a13e80fea34ca751c79fe8dcf68d93d91d4956818baf0b99d95818010002e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000e8764817000000faaa0f339e0fb33f91697cbf5aac41d17921222ae72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60008997b2270000002d9a070d388aa24d9f639bc8ddf985dc473c75d70141401a07d186fdfe3f9862c873d7cd9bdcb9cc8b3f5edcf853af31addcc4476d7d4fe89385cc955a4f604c667110332c14cb2fd8f62a29569b01a572774c7f7136572321026aeca2aed2094e9622a44cf584c694554f10cdb84d4f8eeab3e28ead4e87c168ac'))
        reader2 = BinaryReader(ms2)
        vout_tx = Transaction.DeserializeFrom(reader2)

        self.assertEqual(tx.ToArray(), self.sttx)
        self.assertEqual(tx.Hash.ToBytes(), self.sttx_id)

        with patch('neo.Core.Blockchain.Blockchain.GetTransaction', return_value=(vout_tx, 0)):
            json = tx.ToJson()
        self.assertEqual(json['size'], 191)
        self.assertEqual(json['type'], "StateTransaction")
        self.assertEqual(json['version'], 0)
        self.assertEqual(len(json['attributes']), 0)
        self.assertEqual(len(json['vout']), 0)
        self.assertEqual(len(json['vin']), 1)
        self.assertEqual(json['sys_fee'], "1000")
        self.assertEqual(json['net_fee'], "0")

        descriptors = json['descriptors'][0]
        self.assertEqual(descriptors['type'], "Validator")
        self.assertEqual(descriptors['key'], "025bdf3f181f53e9696227843950deb72dcd374ded17c057159513c3d0abe20b64")
        self.assertEqual(descriptors['field'], "Registered")
        self.assertEqual(descriptors['value'], "01")

    giant_tx_hash = "9af1fcaab6fec80922e25dbea34c534c743dcf8d10f76af1892526c2879d3a70"

    def test_tx_big_remark(self):
        path = '%s/fixtures/bigtx.txt' % os.getcwd()

        with open(path, 'rb') as f:
            blockraw = f.read().strip()

            unhex = binascii.unhexlify(blockraw)

            mstream = StreamManager.GetStream(unhex)
            reader = BinaryReader(mstream)

            tx = Transaction.DeserializeFrom(reader)

            self.assertEqual(tx.Hash.ToString(), self.giant_tx_hash)

    rtx = b'800002900e5468697320697320612074657374900e546869732069732061207465737400019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc326fc500a3e111000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec000'

    def test_GetScriptHashesForVerifying_invalid_operation(self):
        # test a normal tx with a bad assetId
        ms = MemoryStream(binascii.unhexlify(self.rtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        snapshot = GetBlockchain()._db.createSnapshot()
        with self.assertRaises(Exception) as e:
            tx.GetScriptHashesForVerifying(snapshot)

        self.assertTrue("Invalid operation" in str(e.exception))

        # test a raw tx with a bad assetId
        ms = MemoryStream(binascii.unhexlify(self.rtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx.raw_tx = True

        snapshot = GetBlockchain()._db.createSnapshot()
        with self.assertRaises(Exception) as e:
            tx.GetScriptHashesForVerifying(snapshot)

        self.assertTrue("Invalid operation" in str(e.exception))

    drtx = b'800001900e546869732069732061207465737400019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500a3e111000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec000'

    def test_GetScriptHashesForVerifying_DutyFlag(self):
        # test a raw tx
        ms = MemoryStream(binascii.unhexlify(self.rtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx.raw_tx = True

        # create the mocked asset
        mock_asset = AssetState()
        mock_asset.AssetType = 0x80

        snapshot = GetBlockchain()._db.createSnapshot()
        with patch("neo.Core.Helper.Helper.StaticAssetState", return_value=mock_asset):
            res = tx.GetScriptHashesForVerifying(snapshot)

        self.assertTrue(type(res), list)
        self.assertEqual(res[0], Helper.AddrStrToScriptHash("AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"))

    ntx = b'80000190274d792072617720636f6e7472616374207472616e73616374696f6e206465736372697074696f6e01949354ea0a8b57dfee1e257a1aedd1e0eea2e5837de145e8da9c0f101bfccc8e0100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500a3e11100000000ea610aa6db39bd8c8556c9569d94b5e5a5d0ad199b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5004f2418010000001cc9c05cefffe6cdd7b182816a9152ec218d2ec000'
    gtx = b'80000190274d792072617720636f6e7472616374207472616e73616374696f6e206465736372697074696f6e01949354ea0a8b57dfee1e257a1aedd1e0eea2e5837de145e8da9c0f101bfccc8e010002e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000a3e11100000000ea610aa6db39bd8c8556c9569d94b5e5a5d0ad19e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60e05c9041000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec000'

    def test_GetScriptHashesForVerifying_neo_gas(self):
        # test a raw tx using neo
        ms = MemoryStream(binascii.unhexlify(self.ntx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx.raw_tx = True

        snapshot = GetBlockchain()._db.createSnapshot()
        res = tx.GetScriptHashesForVerifying(snapshot)

        self.assertTrue(type(res), list)

        # test a raw tx using gas
        ms = MemoryStream(binascii.unhexlify(self.gtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx.raw_tx = True

        res = tx.GetScriptHashesForVerifying(snapshot)

        self.assertTrue(type(res), list)

    def test_invocation_txn_size(self):
        """ For more information about the following test read here
            https://github.com/neo-project/neo/issues/652
        """
        raw_tx = b"d1015904802b530b14d5a682e81b8a840cc44b3b360cbd0f1ee6f50efd14235a717ed7ed18a43de47499c3d05b8d4a4bcf3a53c1087472616e7366657267fb1c540417067c270dee32f21023aa8b9b71abcef166fc47646b02d3f92300000000000000000120235a717ed7ed18a43de47499c3d05b8d4a4bcf3a0000014140b9234cad658c4d512bca453908a0df1c2beda49c544ec735bb492b81b4d0974ac8d66046061b3d0ce823e27c71fef1ee6a8f2fa369198ac74acedd045901d7222321030ab39b99d8675cd9bd90aaec37cba964297cc817078d33e508ab11f1d245c068ac"
        raw_tx_id = b"c4bb9b638da2e5f4a88ffcc4cb1d4f6693e7f19b7f78d242068254a6c77721f9"  # see https://neoscan.io/transaction/C4BB9B638DA2E5F4A88FFCC4CB1D4F6693E7F19B7F78D242068254A6C77721F9

        mstream = StreamManager.GetStream(binascii.unhexlify(raw_tx))
        reader = BinaryReader(mstream)

        tx = Transaction.DeserializeFrom(reader)
        mstream.Cleanup()

        self.assertEqual(tx.ToArray(), raw_tx)
        self.assertEqual(tx.Hash.ToBytes(), raw_tx_id)

        txjson = tx.ToJson()
        self.assertEqual(227, txjson['size'])

    def test_check_invocation_tx_size(self):
        """ See original test here
            https://github.com/neo-project/neo/blob/master/neo.UnitTests/UT_InvocationTransaction.cs#L52-L69
        """
        i_tx = InvocationTransaction()
        val = GetByteArray(32, 0x42)
        i_tx.Script = val

        self.assertEqual(i_tx.Version, 0)
        self.assertEqual(len(i_tx.Script), 32)
        self.assertEqual(GetVarSize(i_tx.Script), 33)
        self.assertEqual(i_tx.Size(), 39)

    def test_check_invocation_tx_ToJson(self):
        """ See original test here
            https://github.com/neo-project/neo/blob/master/neo.UnitTests/UT_InvocationTransaction.cs#L93-L121
        """
        i_tx = InvocationTransaction()
        val = GetByteArray(32, 0x42)
        i_tx.Script = val
        gasVal = Fixed8.FromDecimal(42)
        i_tx.Gas = gasVal

        jsn = i_tx.ToJson()
        self.assertTrue(jsn)
        self.assertEqual(jsn['txid'], "0x8258b950487299376f89ad2d09598b7acbc5cde89b161b3dd73c256f9e2a94b1")
        self.assertEqual(jsn['size'], 39)
        self.assertEqual(jsn['type'], "InvocationTransaction")
        self.assertEqual(jsn['version'], 0)
        self.assertEqual(len(jsn['attributes']), 0)
        self.assertEqual(len(jsn['vin']), 0)
        self.assertEqual(len(jsn['vout']), 0)
        self.assertEqual(jsn['sys_fee'], "42")
        self.assertEqual(jsn['net_fee'], "-42")
        self.assertEqual(len(jsn['scripts']), 0)
        self.assertEqual(jsn['script'], "4220202020202020202020202020202020202020202020202020202020202020")
        self.assertEqual(jsn['gas'], "42")

    vtx = b"8000000e4737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0d004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0c004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0b004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0a004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c09004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c08004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c07004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c06004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c05004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c04004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c03004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c02004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c01004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0000089b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500bd522a0200000019ae118ef7951731c342d26bbac954c56e8b35d2014140bb549a10e43a86314f2a14046ff486cb1b88857c2cec7bef5a3689490653a9550035ce164ae7adc3ab5b518915c85fef9f4d180dffbb287bd4e399d2e9fdfbd3232103cfb3ad2685ad402dd5122ab83dc1d6a026e8363c905a2c73668825ad2f922d39ac"
    vtx_id = b"af3750da9d8e809fd3980e3d553885726f5c330827fadeaf8af3bbeef1ed3a79"

    def test_verify_exceeds_free_tx_size_less_low_priority_threshhold(self):
        ms = MemoryStream(binascii.unhexlify(self.vtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.vtx)
        self.assertEqual(tx.Hash.ToBytes(), self.vtx_id)

        snapshot = GetBlockchain()._db.createSnapshot()
        res = tx.Verify(snapshot, [tx])
        self.assertFalse(res)

        tx_size = tx.Size()
        self.assertGreater(tx_size, settings.MAX_FREE_TX_SIZE)

        req_fee = Fixed8.FromDecimal(settings.FEE_PER_EXTRA_BYTE * (tx_size - settings.MAX_FREE_TX_SIZE))
        self.assertLess(req_fee, settings.LOW_PRIORITY_THRESHOLD)

        n_fee = tx.NetworkFee()
        self.assertEqual(n_fee.ToString(), '0')
        self.assertLess(n_fee, req_fee)

    vvtx = b"8000000e4737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0d004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0c004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0b004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c0a004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c09004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c08004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c07004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c06004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c05004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c04004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c03004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c02004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c01004737dd0e5247a06ff89160add627a3b614abc76b49eae68f23c5bddc64379d4c00000b9b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f5050000000019ae118ef7951731c342d26bbac954c56e8b35d29b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500fb661e0200000019ae118ef7951731c342d26bbac954c56e8b35d2e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60963de9a80b00000019ae118ef7951731c342d26bbac954c56e8b35d2014140cfbd4ab2822922e8b6941c0c1ed562344dd50e475ca52a88d828d0ed5ab5ca946f11277bf359b1114c94f38662e7a1a65bf9b67b0c6454a620d484eadddfcd58232103cfb3ad2685ad402dd5122ab83dc1d6a026e8363c905a2c73668825ad2f922d39ac"    
    vvtx_id = b"5dccca550ae3e0d52e95a72c5b84b034a3cd4ee6e24cce1f15d85695e2c32209"

    def test_verify_exceeds_free_tx_size_greater_low_priority_threshold(self):
        ms = MemoryStream(binascii.unhexlify(self.vvtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx._network_fee = Fixed8.FromDecimal(0.001)

        self.assertEqual(tx.ToArray(), self.vvtx)
        self.assertEqual(tx.Hash.ToBytes(), self.vvtx_id)

        snapshot = GetBlockchain()._db.createSnapshot()
        res = tx.Verify(snapshot, [tx])
        self.assertFalse(res)

        tx_size = tx.Size()
        self.assertGreater(tx_size, settings.MAX_FREE_TX_SIZE)

        req_fee = Fixed8.FromDecimal(settings.FEE_PER_EXTRA_BYTE * (tx_size - settings.MAX_FREE_TX_SIZE))
        self.assertGreater(req_fee, settings.LOW_PRIORITY_THRESHOLD)

        n_fee = tx.NetworkFee()
        self.assertEqual(n_fee.ToString(), "0.001")
        self.assertLess(n_fee, req_fee)

    def test_verify_exceeds_max_tx_size(self):
        ms = MemoryStream(binascii.unhexlify(self.vvtx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        tx._network_fee = Fixed8.FromDecimal(0.001)

        self.assertEqual(tx.ToArray(), self.vvtx)
        self.assertEqual(tx.Hash.ToBytes(), self.vvtx_id)

        snapshot = GetBlockchain()._db.createSnapshot()

        with patch("neo.Core.TX.Transaction.Transaction.Size", return_value=(Transaction.MAX_TX_SIZE + 1)):
            res = tx.Verify(snapshot, [tx])
            self.assertFalse(res)

            tx_size = tx.Size()
            self.assertGreater(tx_size, Transaction.MAX_TX_SIZE)

    def test_verify_claim_tx_high_priority(self):
        ms = MemoryStream(binascii.unhexlify(self.cltx))
        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)

        self.assertEqual(tx.ToArray(), self.cltx)
        self.assertEqual(tx.Hash.ToBytes(), self.cltx_id)
        snapshot = GetBlockchain()._db.createSnapshot()

        with patch("neo.Core.TX.Transaction.Transaction.Size", return_value=(settings.MAX_FREE_TX_SIZE + 1)):
            with patch('neo.SmartContract.Helper.Helper.VerifyWitnesses', return_value=True):  # we are not testing VerifyScripts
                with patch('neo.Core.Blockchain.Blockchain.CalculateBonusIgnoreClaimed', return_value=Fixed8.FromDecimal(0.30551243)):
                    res = tx.Verify(snapshot, [tx])
                    self.assertTrue(res)

                    tx_size = tx.Size()
                    self.assertGreater(tx_size, settings.MAX_FREE_TX_SIZE)


def GetByteArray(length, firstByte):
    array = bytearray(length)
    array[0] = firstByte
    i = 1
    while i < length:
        array[i] = 0x20
        i += 1
    return array
