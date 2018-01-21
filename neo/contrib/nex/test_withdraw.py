from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.Transaction import ContractTransaction
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neo.Implementations.Wallets.peewee.Models import VINHold
from neo.contrib.nex.withdraw import WithdrawAll, WithdrawOne, PrintHolds,\
    CleanupCompletedHolds, ShowCompletedHolds, RequestWithdrawFrom, DeleteHolds
import json


class WithdrawWalletTestCase(WalletFixtureTestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/withdraw_fixture.tar.gz'
    FIXTURE_FILENAME = './Chains/withdraw_fixture.tar.gz'

    @classmethod
    def leveldb_testpath(self):
        return './withdraw_fixtures'

    @classmethod
    def wallet_1_path(cls):
        return './fixtures/withdraw_wallet.db3'

    @classmethod
    def wallet_1_dest(cls):
        return './withdraw_wallet.db3'

    @classmethod
    def wallet_1_pass(cls):
        return 'testpassword'

    @classmethod
    def wallet_2_path(cls):
        return './fixtures/withdraw_wallet2.db3'

    @classmethod
    def wallet_2_dest(cls):
        return './withdraw_wallet2.db3'

    @classmethod
    def wallet_2_pass(cls):
        return 'testpassword'

    _wallet1 = None

    _wallet2 = None

    wallet_1_script_hash = UInt160(data=b')\x96S\xb5\xe3e\xcb3\xb4\xea:\xd1\xd7\xe1\xb3\xf5\xe6\x81N/')

    wallet_1_addr = 'AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs'

    wallet_2_script_hash = UInt160(data=b'4\xd0=k\x80TF\x9e\xa8W\x83\xfa\x9eIv\x0b\x9bs\x9d\xb6')

    wallet_2_addr = 'ALb8FEhEmtSqv97fuNVuoLmcmrSKckffRf'

    withdraw_hash = 'c5a6485dc64174e1ced6ac041b6b591074f795e4'

    @property
    def GAS(self):
        return Blockchain.Default().SystemCoin().Hash

    @property
    def NEO(self):
        return Blockchain.Default().SystemShare().Hash

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(WithdrawWalletTestCase.wallet_1_dest(), WithdrawWalletTestCase.wallet_1_pass())
        return cls._wallet1

    @classmethod
    def GetWallet2(cls, recreate=False):
        if cls._wallet2 is None or recreate:
            cls._wallet2 = UserWallet.Open(WithdrawWalletTestCase.wallet_2_dest(), WithdrawWalletTestCase.wallet_2_pass())
        return cls._wallet2

    def test_1_initial_setup(self):

        wallet = self.GetWallet1()

        self.assertEqual(wallet.WalletHeight, 203437)

        holds = wallet._holds

        self.assertEqual(len(holds), 2)

        count = 0

        for item in holds:  # type:VINHold

            self.assertIsInstance(item, VINHold)
            self.assertFalse(item.IsComplete)
            self.assertIsInstance(item.OutputHash, UInt160)
            self.assertIsInstance(item.InputHash, UInt160)
            self.assertEqual(item.OutputHash, self.wallet_1_script_hash)
            self.assertIsInstance(item.TXHash, UInt256)

            if count == 0:
                # item is the last one
                self.assertEqual(item.Vin, bytearray(b'\x81\xae\x0bPmK\xda`OT\x0f\xf2\x95\x9b\x07\x08I]N\x1dW\x9bp\xe8\xcd\x16\n \xfbu\xaf\x17\x00'))
            count += 1

        completed = wallet.LoadCompletedHolds()

        self.assertEqual(len(completed), 1)
        completed_hold = completed[0]  # type:VINHold

        self.assertTrue(completed_hold.IsComplete, True)

    def test_2_print(self):

        wallet = self.GetWallet1()

        ShowCompletedHolds(wallet)
        PrintHolds(wallet)

    def test_3_make_withdrawl_request(self):

        wallet = self.GetWallet1()

        res = RequestWithdrawFrom(wallet, 'neo', self.withdraw_hash, self.wallet_1_addr, 100)

        self.assertFalse(res)

        res2 = RequestWithdrawFrom(wallet, 'neo', self.withdraw_hash, self.wallet_1_addr, 1, require_password=False)

        self.assertIsInstance(res2, InvocationTransaction)

        self.assertEqual(res2.Hash.ToString(), '828a161d718890c7de29527f5c8c705cba1abb17bc627f76681800e78a49e200')

    def test_4_withdraw_one(self):

        wallet = self.GetWallet1()

        res = WithdrawOne(wallet, require_password=False)

        self.assertIsInstance(res, ContractTransaction)

        self.assertEqual(res.Hash.ToString(), '505e0d6cc4302fb119ec21edbb40bfc17fa7dd6083586390843c0a07bea15fc8')

    def test_5_withdraw_all(self):

        wallet = self.GetWallet1(recreate=True)

        res = WithdrawAll(wallet, require_password=False)

        self.assertTrue(res)

    def test_6_cleanup_holds(self):

        wallet = self.GetWallet1()

        res = CleanupCompletedHolds(wallet, require_password=False)

        self.assertIsInstance(res, InvocationTransaction)

        self.assertEqual(res.Hash.ToString(), 'aa27a2331631e7594517fed5f6388e6f3e2567a7854b4d98901c818d9f20d03e')

    def test_7_delete_holds(self):

        wallet = self.GetWallet1(recreate=True)

        DeleteHolds(wallet, index_to_delete=-1)

        wallet.LoadHolds()

        self.assertEqual(wallet._holds, [])
