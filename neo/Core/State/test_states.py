import json
import binascii

from neo.Utils.NeoTestCase import NeoTestCase
from neo.Core.State.SpentCoinState import SpentCoinState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AccountState import AccountState
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Core.Blockchain import Blockchain


class StateTestCase(NeoTestCase):

    shash = b"\x89\xeb\x8bV\xf7\x7f\xcd1vs\xdb\xe9\x94\xf0\xc9\x1f\'\xb9\xca\xaf"
    saddr = 'AUM8Pgc9QTgRBcmGppYoVZ6TFn5UpPDXFs'

    def test_account_state(self):
        hash = UInt160(data=self.shash)
        account = AccountState(script_hash=hash)

        addr = account.Address

        self.assertEqual(addr, self.saddr)

        input = binascii.unhexlify(self.assset)

        asset = AssetState.DeserializeFromDB(input)

        account.AddToBalance(asset.AssetId, Fixed8(2440000000))

        self.assertEqual(account.BalanceFor(asset.AssetId), Fixed8(2440000000))

        account.SubtractFromBalance(asset.AssetId, Fixed8(1220000000))

        self.assertEqual(account.BalanceFor(asset.AssetId), Fixed8(1220000000))

        self.assertEqual(account.HasBalance(asset.AssetId), True)

        sshare_hash = Blockchain.SystemShare().Hash

        account.SubtractFromBalance(sshare_hash, Fixed8(800000000))

        self.assertFalse(account.AllBalancesZeroOrLess())

        acct_json = account.ToJson()

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)

        account.Serialize(writer)
        out = stream.ToArray()
        StreamManager.ReleaseStream(stream)

        input = binascii.unhexlify(out)
        newaccount = AccountState.DeserializeFromDB(input)

        self.assertEqual(acct_json, newaccount.ToJson())

    ac1_out = b'0089eb8b56f77fcd317673dbe994f0c91f27b9caaf0000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500f850d0ffffffffe72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000b9b74800000000'

    ac2_h = b'\xf3\x97\x1c\xa1\x1e\xc9\xd8j\xba}\x9b8\xc6#\xe0<Ds\r\xd1'
    ac2_a = 'AdyrsYhdmiV2fPshxX3esXFbzJ1XNmvhYJ'

    def test_account_2(self):

        hash = UInt160(data=self.ac2_h)
        account2 = AccountState(script_hash=hash)

        addr = account2.Address

        self.assertEqual(addr, self.ac2_a)

        input = binascii.unhexlify(self.assset)
        asset = AssetState.DeserializeFromDB(input)

        account2.AddToBalance(asset.AssetId, Fixed8(97800000000))

#        print("account 2 %s " % json.dumps(account2.ToJson(), indent=4))

        self.assertEqual(account2.BalanceFor(asset.AssetId), Fixed8(97800000000))

        input = binascii.unhexlify(self.ac1_out)
        account1 = AccountState.DeserializeFromDB(input)

#        print("account 1 %s " % json.dumps(account1.ToJson(), indent=4))

    assset = b'00e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6001445b7b226c616e67223a227a682d434e222c226e616d65223a22e5b08fe89a81e5b881227d2c7b226c616e67223a22656e222c226e616d65223a22416e74436f696e227d5d0000c16ff28623000000000000000000080000000000000000000000000000000000000000000000000000000000009f7fd096d37ed2c0e3f7f0cfc924beef4ffceb689f7fd096d37ed2c0e3f7f0cfc924beef4ffceb6800093d0000'
    assetkey = b'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'

    def test_asset_state(self):
        input = binascii.unhexlify(self.assset)

        asset = AssetState.DeserializeFromDB(input)

        self.assertEqual(asset.GetName(), 'NEOGas')
        self.assertEqual(asset.AssetId.ToBytes(), self.assetkey)
        self.assertEqual(asset.Precision, 8)
        self.assertEqual(asset.Admin.ToBytes(), b'68ebfc4fefbe24c9cff0f7e3c0d27ed396d07f9f')
        self.assertEqual(asset.Issuer.ToBytes(), b'68ebfc4fefbe24c9cff0f7e3c0d27ed396d07f9f')
        self.assertEqual(asset.IsFrozen, False)
        self.assertTrue(asset.Owner.IsInfinity)

        self.assertIsNotNone(asset.ToJson())

    sckey = b'617cafec2da972f17afc66b1b30b412539a5e3caa9f74afadcbd45b7a1dae5a7'
    scbuffer = b'007cafec2da972f17afc66b1b30b412539a5e3caa9f74afadcbd45b7a1dae5a7006121a40201000025a40200'

    def test_spentcoin(self):

        input = binascii.unhexlify(self.scbuffer)

        spentcoin = SpentCoinState.DeserializeFromDB(input)

        self.assertEqual(spentcoin.TransactionHash.ToBytes(), b'00a7e5daa1b745bddcfa4af7a9cae3a53925410bb3b166fc7af172a92decaf7c')

        self.assertEqual(len(spentcoin.Items), 1)

        self.assertEqual(spentcoin.Items[0].height, 173093)

        self.assertEqual(spentcoin.TransactionHeight, 44310881)

        json = spentcoin.ToJson()

        self.assertIsNotNone(json)

    ctr = b'00fd4401746b4c04000000004c04000000004c04000000006161681e416e745368617265732e426c6f636b636861696e2e47657448656967687461681d416e745368617265732e426c6f636b636861696e2e476574426c6f636b744c0400000000948c6c766b947275744c0400000000936c766b9479744c0400000000948c6c766b947961681d416e745368617265732e4865616465722e47657454696d657374616d70a0744c0401000000948c6c766b947275744c0401000000948c6c766b9479641b004c0400000000744c0402000000948c6c766b947275623200744c0401000000936c766b9479744c0402000000936c766b9479617cac744c0402000000948c6c766b947275620300744c0402000000948c6c766b947961748c6c766b946d748c6c766b946d748c6c766b946d746c768c6b946d746c768c6b946d746c768c6b946d6c7566030205000100044c6f636b0e312e302e302d70726576696577320a4572696b205a68616e67126572696b40616e747368617265732e6f7267234c6f636b20796f75722061737365747320756e74696c20612074696d657374616d702e'
    ctr_script = b'746b4c04000000004c04000000004c04000000006161681e416e745368617265732e426c6f636b636861696e2e47657448656967687461681d416e745368617265732e426c6f636b636861696e2e476574426c6f636b744c0400000000948c6c766b947275744c0400000000936c766b9479744c0400000000948c6c766b947961681d416e745368617265732e4865616465722e47657454696d657374616d70a0744c0401000000948c6c766b947275744c0401000000948c6c766b9479641b004c0400000000744c0402000000948c6c766b947275623200744c0401000000936c766b9479744c0402000000936c766b9479617cac744c0402000000948c6c766b947275620300744c0402000000948c6c766b947961748c6c766b946d748c6c766b946d748c6c766b946d746c768c6b946d746c768c6b946d746c768c6b946d6c7566'
    ctr_hash = b'54030ae64f0a6d24bfda562778e0f4c9f1e24ecc'

    def test_contract(self):

        input = (binascii.unhexlify(self.ctr))

        contract = ContractState.DeserializeFromDB(input)

        self.assertEqual(contract.Name.decode('utf-8'), 'Lock')
        self.assertEqual(contract.Author.decode('utf-8'), 'Erik Zhang')
        self.assertEqual(contract.Description.decode('utf-8'), 'Lock your assets until a timestamp.')
        self.assertEqual(contract.Email.decode('utf-8'), 'erik@antshares.org')
        self.assertEqual(contract.HasStorage, False)
        self.assertEqual(contract.CodeVersion.decode('utf-8'), '1.0.0-preview2')

        self.assertIsNotNone(contract.Code)

        self.assertEqual(binascii.hexlify(contract.Code.Script), self.ctr_script)
        self.assertEqual(contract.Code.ScriptHash().ToBytes(), self.ctr_hash)
