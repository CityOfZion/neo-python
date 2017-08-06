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

        self.assertEqual(tx.HashToByteString(), self.tx_id)

        self.assertEqual(tx.Nonce, self.tx_nonce)

        self.assertEqual(tx.inputs, [])
        self.assertEqual(tx.outputs, [])
        self.assertEqual(tx.scripts, [])


        ms = MemoryStream()
        writer = BinaryWriter(ms)

        tx.Serialize(writer)
        out = ms.ToArray()

        self.assertEqual(out, self.tx_raw)


    ctx_raw = b'800000014a4dfb91023b1b2086029e03af739d9ceab35fffa8d528de9a6fee3e62bbecbd0000019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50000c16ff286230067f97110a66136d38badc7b9f88eab013027ce4901fd04014099546819767644bbef323e428aab48c8801e66b8c7fb452dcd11205c13f5b198c9b37e9aa6808d6c3a74e50931d3413115e2a86a4a4a99fcae894219c092ca6340a0de35bc6c04c25b8f6cca46b91a35144db40fc94967293500f08c58df81f7c9ecb59cc13bcaca4d932e27a8d9a8204f48d488b6ccdfccd830c22bf4b7353dd64039346418372b541dfe7fdc99611bfc59cee881044da2912cb2404b885c6472310a2b771153e6a0022abb11aa41288ef98a2aed1bb42714fa6a1c6e85e415b8bb4045cc681dbe07155b554b0291f0352546223e49e3192c221249c29eb97651aec3c5f2f6adfc85a87cfdfef3a15d57391cf99190e8d80b01fcc1ebf8f48c745957f154210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae'
    ctx_id = b'4feb0081f9425cab84269127bef0a871a84d4408f09923d17ebb257cd231b362'

    def test_contract_tx_deserialize(self):

        ms = MemoryStream(binascii.unhexlify(self.ctx_raw))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)


        self.assertEqual(tx.ToArray(), self.ctx_raw)

        self.assertEqual(tx.HashToByteString(), self.ctx_id)


    pb_raw = b'd000fd3f01746b4c04000000004c04000000004c040000000061681e416e745368617265732e426c6f636b636861696e2e476574486569676874681d416e745368617265732e426c6f636b636861696e2e476574426c6f636b744c0400000000948c6c766b947275744c0402000000936c766b9479744c0400000000948c6c766b9479681d416e745368617265732e4865616465722e47657454696d657374616d70a0744c0401000000948c6c766b947275744c0401000000948c6c766b9479641b004c0400000000744c0402000000948c6c766b947275623000744c0401000000936c766b9479744c0400000000936c766b9479ac744c0402000000948c6c766b947275620300744c0402000000948c6c766b947961748c6c766b946d748c6c766b946d748c6c766b946d746c768c6b946d746c768c6b946d746c768c6b946d6c75660302050001044c6f636b0c312e302d70726576696577310a4572696b205a68616e67126572696b40616e747368617265732e6f7267234c6f636b20796f75722061737365747320756e74696c20612074696d657374616d702e00014e23ac4c4851f93407d4c59e1673171f39859db9e7cac72540cd3cc1ae0cca87000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000ebcaaa0d00000067f97110a66136d38badc7b9f88eab013027ce49014140c298da9f06d5687a0bb87ea3bba188b7dcc91b9667ea5cb71f6fdefe388f42611df29be9b2d6288655b9f2188f46796886afc3b37d8b817599365d9e161ecfb62321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    pb_hash = b'5467a1fc8723ceffa8e5ee59399b02eea1df6fbaa53768c6704b90b960d223fa'

    def test_publish_tx_deserialize(self):

        ms = MemoryStream(binascii.unhexlify(self.pb_raw))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.pb_raw)
        self.assertEqual(tx.HashToByteString(), self.pb_hash)


    ir = b'd100644011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111081234567890abcdef0415cd5b0769cc4ee2f1c9f4e0782756dabf246d0a4fe60a035400000000'
    ir_id=b'1a328cdd53c7f1710b4006304e8c75236a9b18523f037cdf069a96f0d7f01379'

    def test_invocation_transaction(self):

        ms = MemoryStream(binascii.unhexlify(self.ir))

        reader = BinaryReader(ms)

        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.ToArray(), self.ir)
        self.assertEqual(tx.HashToByteString(), self.ir_id)


    mr = b'00006666654200000000'
    mrn = 1113941606
    mrh = b'4c68669a54fa247d02545cff9d78352cb4a5059de7b3cd6ba82efad13953c9b9'
    def test_miner_tx(self):

        ms = MemoryStream(binascii.unhexlify(self.mr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        print("tx: %s " % tx.HashToByteString())
        self.assertEqual(tx.Nonce, self.mrn)
        self.assertEqual(tx.ToArray(), self.mr)
        self.assertEqual(tx.HashToByteString(), self.mrh)


    rr = b'400060245b7b226c616e67223a227a682d434e222c226e616d65223a2254657374436f696e227d5dffffffffffffffff08034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e1167f97110a66136d38badc7b9f88eab013027ce4900014423a26aeca49cdeeb9522c720e1ae3a93bbe27d53662839b16a438305c20906010001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60001e1a210b00000067f97110a66136d38badc7b9f88eab013027ce490141405d8223ec807e3416a220a75ef9805dfa2e36bd4f6dcc7372373aa45f15c7fadfc96a8642e52acf56c2c66d549be4ba820484873d5cada00b9c1ce9674fbf96382321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    rrid = b'0c092117b4ba47b81001712425e6e7f760a637695eaf23741ba335925b195ecd'


    def test_register_tx(self):

        ms = MemoryStream(binascii.unhexlify(self.rr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        print("tx: %s " % tx.HashToByteString())
        self.assertEqual(self.rrid, tx.HashToByteString())

    cr = b'800001f012e99481e4bb93e59088e7baa6e6b58be8af9502f8e0bc69b6af579e69a56d3d3d559759cdb848cb55b54531afc6e3322c85badf08002c82c09c5b49d10cd776c8679789ba98d0b0236f0db4dc67695a1eb920a646b9000001cd5e195b9235a31b7423af5e6937a660f7e7e62524710110b847bab41721090c0061c2540cd1220067f97110a66136d38badc7b9f88eab013027ce490241400bd2e921cee90c8de1a192e61e33eb8980a3dc00c388ee9aac0712178cc8fceed8bb59788f7caf3c4dc082abcdaaa49772fda86db4ceea243bda31bcde9b8a0b3c21034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e1104182f145967cc4ee2f1c9f4e0782756dabf246d0a4fe60a035441402fe3e20c303e26c3817fed6fc7db8edde4ac62b16eee796c01c2b59e382b7ddfc82f0b36c7f7520821c7b72b9aff50ae27a016961f1ef1dade9cafa85655380f2321034b44ed9c8a88fb2497b6b57206cc08edd42c5614bd1fee790e5b795dee0f4e11ac'
    crid = b'e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff178'


    def test_contract_tx_again(self):
        ms = MemoryStream(binascii.unhexlify(self.cr))

        reader = BinaryReader(ms)
        tx = Transaction.DeserializeFrom(reader)
        self.assertEqual(tx.HashToByteString(), self.crid)
