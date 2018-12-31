from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.BuildNRun import BuildAndRun
from neo.Wallets.utils import to_aes_key
from neo.Settings import settings


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    big_str = "b'abababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababababab'"

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put", "key1", "b'ab'", "--from-addr=" + self.wallet_1_addr]

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put_5", "key1", "b'abababababab'"]

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put_and_get", "key1", "b'abababababab'"]

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put_and_get", "key1", self.big_str]

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put_5", "key1", self.big_str]

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

        arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "True", "070705", "05", "put_9", "key1", "b'ababababab'"]

        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False)

        expected_cost = Fixed8.FromDecimal(9.762)
        expected_gas = Fixed8.FromDecimal(.0001)
        self.assertEqual(expected_cost, engine.GasConsumed())
        self.assertEqual(tx.Gas, expected_gas)

    def test_build_contract_7(self):
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
        with self.assertRaises(TypeError):
            wallet = self.GetWallet1()

            arguments = ["neo/SmartContract/tests/StorageTest.py", "True", "False", "070705", "05", "put_5", "key1", self.big_str]

            tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False, invocation_test_mode=False)

#           expected_cost = Fixed8(1046600000)
#           expected_gas = Fixed8.FromDecimal(1.0)
