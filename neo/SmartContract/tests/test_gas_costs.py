from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.BuildNRun import BuildAndRun

class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
    _wallet1 = None

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(), UserWalletTestCase.wallet_1_pass())
        return cls._wallet1


    def test_build_contract(self):

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put", "key1" ,"b'ab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet)

        expected_cost = Fixed8.FromDecimal(1.056)

        self.assertEqual(expected_cost, engine.GasConsumed())


    def test_build_contract_2(self):

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_5", "key1" ,"b'abababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet)

        expected_cost = Fixed8.FromDecimal(6.151)

        self.assertEqual(expected_cost, engine.GasConsumed())



    def test_build_contract_3(self):

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_and_get", "key1" ,"b'abababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet)

        expected_cost = Fixed8.FromDecimal(1.18)

        self.assertEqual(expected_cost, engine.GasConsumed())


