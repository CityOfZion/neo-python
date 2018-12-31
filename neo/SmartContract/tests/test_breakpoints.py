from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.BuildNRun import BuildAndRun
from neo.Wallets.utils import to_aes_key
from neo.Settings import settings
from mock import MagicMock
from neo.Prompt.vm_debugger import VMDebugger, DebugContext


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

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

    def test_debug_contract_1(self):

        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/BreakpointTest.py", "True", "False", "True", "02", "01", "1", ]
        dbg = VMDebugger
#        dbg.end = MagicMock(return_value=None)
        dbg.start = MagicMock(return_value=None)
        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False, min_fee=Fixed8.FromDecimal(.0004))

        debugger = engine._vm_debugger
        context = debugger.get_context()
        context.print_file()
        self.assertIsInstance(debugger, VMDebugger)
        self.assertIsInstance(context, DebugContext)

        self.assertEqual(debugger.index, 29)
        self.assertEqual(context.method.name, 'Main')
        self.assertEqual(context.line, 11)

    def test_debug_contract_2(self):
        wallet = self.GetWallet1()

        arguments = ["neo/SmartContract/tests/BreakpointTest.py", "True", "False", "True", "02", "01", "4", ]
        dbg = VMDebugger
        #        dbg.end = MagicMock(return_value=None)
        dbg.start = MagicMock(return_value=None)
        tx, result, total_ops, engine = BuildAndRun(arguments, wallet, False, min_fee=Fixed8.FromDecimal(.0004))

        debugger = engine._vm_debugger
        context = debugger.get_context()
        context.print()
        self.assertEqual(debugger.index, 157)
        self.assertEqual(context.method.name, 'another_method')
        self.assertEqual(context.line, 38)
