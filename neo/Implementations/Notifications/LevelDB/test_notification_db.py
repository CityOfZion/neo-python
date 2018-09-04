from unittest import TestCase
from neo.Settings import settings
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neo.SmartContract.ContractParameter import ContractParameterType, ContractParameter
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from uuid import uuid1
import shutil
import os

from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neocore.BigInteger import BigInteger


class NotificationDBTestCase(TestCase):

    contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    event_tx = UInt256(data=bytearray(b'\x90\xe4\xf1\xbbb\x8e\xf1\x07\xde\xe9\xf0\xd2\x12\xd1w\xbco\x844\x07=\x1b\xa7\x1f\xa7\x94`\x0b\xb4\x88|K'))

    addr_to = b')\x96S\xb5\xe3e\xcb3\xb4\xea:\xd1\xd7\xe1\xb3\xf5\xe6\x81N/'
    addr_from = b'4\xd0=k\x80TF\x9e\xa8W\x83\xfa\x9eIv\x0b\x9bs\x9d\xb6'

    @classmethod
    def setUpClass(cls):

        settings.NOTIFICATION_DB_PATH = os.path.join(settings.DATA_DIR_PATH,
                                                     f"fixtures/{str(uuid1())}")
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        NotificationDB.instance().close()
        shutil.rmtree(settings.NOTIFICATION_DB_PATH)

    def test_1_notify_should_not_persist(self):

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, ContractParameter(ContractParameterType.Array, []), self.contract_hash, 99, self.event_tx, True, False)

        ndb = NotificationDB.instance()
        ndb.on_smart_contract_event(sc)

        self.assertEqual(ndb.current_events, [])

    def test_2_persist_isnt_notify_event(self):
        sc = SmartContractEvent(SmartContractEvent.RUNTIME_NOTIFY, ContractParameter(ContractParameterType.Array, []), self.contract_hash, 99, self.event_tx, True, False)

        ndb = NotificationDB.instance()
        ndb.on_smart_contract_event(sc)

        self.assertEqual(ndb.current_events, [])

    def test_3_should_persist(self):
        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'transfer'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.ByteArray, self.addr_from),
            ContractParameter(ContractParameterType.Integer, 123000)
        ])
        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, False)

        ndb = NotificationDB.instance()
        ndb.on_smart_contract_event(sc)

        self.assertEqual(len(ndb.current_events), 1)
        ndb.on_persist_completed(None)

    def test_4_should_persist(self):

        ndb = NotificationDB.instance()

        self.assertEqual(len(ndb.current_events), 0)

        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'transfer'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.ByteArray, self.addr_from),
            ContractParameter(ContractParameterType.Integer, 123000)
        ])

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, True)

        ndb.on_smart_contract_event(sc)

        self.assertEqual(len(ndb.current_events), 0)

    def test_4_notification_lookup(self):

        ndb = NotificationDB.instance()

        events = ndb.get_by_block(91349)

        self.assertEqual(len(events), 1)

    def test_5_addr_from_lookup(self):
        ndb = NotificationDB.instance()

        events = ndb.get_by_addr('ALb8FEhEmtSqv97fuNVuoLmcmrSKckffRf')

        self.assertEqual(len(events), 1)

        evt = events[0]  # type:NotifyEvent

        self.assertEqual(evt.AddressTo, 'ALb8FEhEmtSqv97fuNVuoLmcmrSKckffRf')

    def test_6_addr_to_lookup(self):
        ndb = NotificationDB.instance()

        events = ndb.get_by_addr('AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs')

        self.assertEqual(len(events), 1)

        evt = events[0]  # type:NotifyEvent

        self.assertEqual(evt.AddressFrom, 'AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs')

    def test_7_lookup_addr_by_script_hash(self):

        ndb = NotificationDB.instance()

        sh = UInt160(data=b')\x96S\xb5\xe3e\xcb3\xb4\xea:\xd1\xd7\xe1\xb3\xf5\xe6\x81N/')

        events = ndb.get_by_addr(sh)

        self.assertEqual(len(events), 1)

    def test_8_lookup_should_be_empty(self):

        ndb = NotificationDB.instance()

        events = ndb.get_by_block(123)

        self.assertEqual(len(events), 0)

    def test_9_lookup_should_be_empty(self):

        ndb = NotificationDB.instance()

        sh = UInt160(data=b')\x96S\xb5\xe3e\xcb3\xb4\xea:\xd1\xd7\xe1\xb3\xf5\xe6\x82N/')

        events = ndb.get_by_addr(sh)

        self.assertEqual(len(events), 0)

    def test_should_persist_mint_event(self):

        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'mint'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.Integer, 123000)
        ])

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, False)

        ndb = NotificationDB.instance()
        ndb.on_smart_contract_event(sc)

        self.assertEqual(len(ndb.current_events), 1)
        ndb.on_persist_completed(None)
