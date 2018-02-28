from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.BuildNRun import BuildAndRun
from neo.Wallets.utils import to_aes_key
from neo.Settings import settings


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
    _wallet1 = None

    big_str = "b'abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab'"

    @classmethod
    def setUpClass(cls):
        super(UserWalletTestCase, cls).setUpClass()
        settings.log_smart_contract_events = True

    @classmethod
    def tearDownClass(cls):
        super(UserWalletTestCase, cls).tearDownClass()
        settings.log_smart_contract_events = False

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(), to_aes_key(UserWalletTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_build_contract(self):
        """
        return from JSON-RPC is:
        {'state': 'HALT, BREAK', 'script': '01ab066b6579313233037075746780a1a5b87921dda4603b502ada749890cbca3434',
        'stack': [{'type': 'Integer', 'value': '1'}], 'gas_consumed': '1.056'}
        """

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put", "key1", "b'ab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False, min_fee=Fixed8.FromDecimal(.0004))

        expected_cost = Fixed8(103900000)
        expected_fee = Fixed8.FromDecimal(.0004)

        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_fee)
        self.assertEqual(bool(result), True)

    def test_build_contract_2(self):
        """
        return from JSON-RPC is:
        {'state': 'HALT, BREAK', 'script': '06abababababab046b657931057075745f356780a1a5b87921dda4603b502ada749890cbca3434',
        'stack': [{'type': 'Integer', 'value': '1'}], 'gas_consumed':'6.151'}
        """

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_5", "key1", "b'abababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8.FromDecimal(5.466)
        expected_fee = Fixed8.FromDecimal(.0001)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_fee)
        self.assertEqual(bool(result), True)

    def test_build_contract_3(self):
        """
        return from JSON-RPC is:

        {'state': 'HALT, BREAK',
         'script': '06abababababab046b6579310b7075745f616e645f6765746780a1a5b87921dda4603b502ada749890cbca3434',
         'stack': [{'type': 'ByteArray', 'value': 'abababababab'}], 'gas_consumed': '1.18'}
        """
        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_and_get", "key1", "b'abababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8.FromDecimal(1.153)
        expected_fee = Fixed8.FromDecimal(.0001)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_fee)
        self.assertEqual(result[0].GetByteArray(), bytearray(b'\xab\xab\xab\xab\xab\xab'))

    def test_build_contract_4(self):
        """
        return from JSON-RPC is:

        {'state': 'HALT, BREAK',
         'script': '06abababababab046b6579310b7075745f616e645f6765746780a1a5b87921dda4603b502ada749890cbca3434',
         'stack': [{'type': 'ByteArray', 'value': 'abababababab'}], 'gas_consumed': '1.18'}
        """
        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_and_get", "key1", self.big_str]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8.FromDecimal(2.153)
        expected_fee = Fixed8.FromDecimal(.0001)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_fee)

    def test_build_contract_5(self):
        """
        return from JSON-RPC is:
        {'state': 'HALT, BREAK', 'script': '4d0004ababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        bababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab
        abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        bababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab
        abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        bababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab
        abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        bababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab
        abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        bababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab
        abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababa
        babababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab046b657931057075745f356780a1a5b87921dda4603b502ada749890cb
        ca3434', 'stack': [{'type': 'Integer', 'value': '1'}], 'gas_consumed': '11.151'}
        """
        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_5", "key1", self.big_str]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8(1046600000)
        expected_gas = Fixed8.FromDecimal(1.0)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_gas)

    def test_build_contract_6(self):
        """
        return from JSON-RPC is:
        {"state":"HALT, BREAK", "result":{"script":"05ababababab046b657931057075745f3867e2cea0ae062d6f13ce53b799e0d4fa6eaa147c38",
        "gas_consumed":"9.715","stack":[{"type":"Integer","value":"1"}]}}
        """
        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/StorageTest.py", "test", "070705", "05", True, False, "put_9", "key1", "b'ababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8.FromDecimal(9.762)
        expected_gas = Fixed8.FromDecimal(.0001)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_gas)
