from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.SmartContract.SmartContractEvent import SmartContractEvent
from neocore.UInt160 import UInt160
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.Wallets.utils import to_aes_key
from neo.Settings import settings
from neo.EventHub import events
from neo.Core.State.ContractState import ContractState
import os


class ContractMigrateTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    @classmethod
    def setUpClass(cls):
        super(ContractMigrateTestCase, cls).setUpClass()
        settings.log_smart_contract_events = True
        settings.USE_DEBUG_STORAGE = True

    @classmethod
    def tearDownClass(cls):
        super(ContractMigrateTestCase, cls).tearDownClass()
        settings.log_smart_contract_events = False

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(ContractMigrateTestCase.wallet_1_dest(), to_aes_key(ContractMigrateTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_build_contract_and_destroy(self):

        items = []
        destroyed_items = []

        def on_created(sc_event):
            items.append(sc_event)

        def on_destroyed(sc_event):
            destroyed_items.append(sc_event)

        events.on(SmartContractEvent.CONTRACT_CREATED, on_created)
        events.on(SmartContractEvent.CONTRACT_DESTROY, on_destroyed)

        output = Compiler.instance().load('%s/MigrateTest1.py' % os.path.dirname(__file__)).default
        script = output.write()

        tx, results, total_ops, engine = TestBuild(script, ['store_data', bytearray(b'\x10')], self.GetWallet1(), '0705', '05')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        self.assertEqual(len(items), 1)

        created_hash = items[0].contract_hash.ToBytes()
        script_table = engine._Table
        self.assertIsNotNone(script_table.GetScript(created_hash))

        tx, results, total_ops, engine = TestBuild(script, ['get_data', bytearray(b'\x10')], self.GetWallet1(), '0705', '05')

        self.assertEqual(len(results), 1)
        mylist = results[0].GetArray()

        self.assertEqual([item.GetByteArray() for item in mylist], [bytearray(b'\x01'), bytearray(b'abc'), bytearray(b'\x01\x02\x03')])

        tx, results, total_ops, engine = TestBuild(script, ['do_destroy', bytearray(b'\x10')], self.GetWallet1(), '0705', '05')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)
        self.assertEqual(len(destroyed_items), 1)

        destroyed_hash = destroyed_items[0].contract_hash.ToBytes()
        script_table = engine._Table
        self.assertIsNone(script_table.GetScript(destroyed_hash))

    def test_build_contract_and_migrate(self):

        items = []
        migrated_items = []

        def on_created(sc_event):
            items.append(sc_event)

        def on_migrated(sc_event):
            migrated_items.append(sc_event)

        events.on(SmartContractEvent.CONTRACT_CREATED, on_created)
        events.on(SmartContractEvent.CONTRACT_MIGRATED, on_migrated)

        output = Compiler.instance().load('%s/MigrateTest1.py' % os.path.dirname(__file__)).default
        script = output.write()
        tx, results, total_ops, engine = TestBuild(script, ['store_data', bytearray(b'\x10')], self.GetWallet1(), '0705', '05')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        self.assertEqual(len(items), 1)

        created_hash = items[0].contract_hash.ToBytes()
        script_table = engine._Table
        self.assertIsNotNone(script_table.GetScript(created_hash))

        migrateScript = Compiler.instance().load('%s/MigrateTest2.py' % os.path.dirname(__file__)).default.write()
        tx, results, total_ops, engine = TestBuild(script, ['do_migrate', migrateScript], self.GetWallet1(), '0705', '05')

        self.assertEqual(len(results), 1)
        new_contract = results[0].GetInterface()
        self.assertIsInstance(new_contract, ContractState)

        self.assertEqual(len(migrated_items), 1)
        self.assertEqual(new_contract, migrated_items[0].event_payload.Value)

        # now make sure the original contract isnt there
        script_table = engine._Table
        self.assertIsNone(script_table.GetScript(created_hash))

        # and make sure the new one is there
        migrated_hash = migrated_items[0].contract_hash

        self.assertIsNotNone(script_table.GetScript(migrated_hash.ToBytes()))

        # now make sure the new contract has the same storage

        tx, results, total_ops, engine = TestBuild(migrateScript, ['i1'], self.GetWallet1(), '07', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetByteArray(), bytearray(b'\x01'))

        tx, results, total_ops, engine = TestBuild(migrateScript, ['s2'], self.GetWallet1(), '07', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetByteArray(), bytearray(b'hello world'))

        tx, results, total_ops, engine = TestBuild(migrateScript, ['i4'], self.GetWallet1(), '07', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 400000000000)
