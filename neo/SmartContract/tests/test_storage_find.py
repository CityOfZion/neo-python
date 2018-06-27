from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.EventHub import events, SmartContractEvent


class TestStorageFind(WalletFixtureTestCase):
    dispatched_events = []
    script = None
    _wallet1 = None

    @classmethod
    def setUpClass(cls):
        super(TestStorageFind, cls).setUpClass()
        f = open('./fixtures/storage_find.avm', 'rb')
        cls.script = f.read()
        f.close()

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(WalletFixtureTestCase.wallet_1_dest(), to_aes_key(WalletFixtureTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_c_sharp_storage_find(self):
        """
        test that c# compiled storage find contract works as expected
        """

        events_emitted = []

        def on_notify(sc_event):
            events_emitted.append(sc_event)

        events.on(SmartContractEvent.RUNTIME_NOTIFY, on_notify)

        tx, results, total_ops, engine = TestBuild(self.script, [], self.GetWallet1(), '', 'ff')

        self.assertEqual(results, [])

        self.assertEqual(len(events_emitted), 4)

        self.assertEqual([b'Starting', b'my_prefixA', b'my_prefixB', b'Done'], [event.event_payload.Value[0].Value for event in events_emitted])
