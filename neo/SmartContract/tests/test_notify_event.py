from unittest import TestCase
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.BigInteger import BigInteger
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryWriter import BinaryWriter
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType


class EventTestCase(TestCase):

    contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    event_tx = UInt256(data=bytearray(b'\x90\xe4\xf1\xbbb\x8e\xf1\x07\xde\xe9\xf0\xd2\x12\xd1w\xbco\x844\x07=\x1b\xa7\x1f\xa7\x94`\x0b\xb4\x88|K'))

    addr_to = b')\x96S\xb5\xe3e\xcb3\xb4\xea:\xd1\xd7\xe1\xb3\xf5\xe6\x81N/'
    addr_from = b'4\xd0=k\x80TF\x9e\xa8W\x83\xfa\x9eIv\x0b\x9bs\x9d\xb6'

    def test_1_serialize_runtime_log(self):

        sc = SmartContractEvent(SmartContractEvent.RUNTIME_LOG, ContractParameter(ContractParameterType.Array, []), self.contract_hash, 99999, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        self.assertEqual(out, b'\x19SmartContract.Runtime.Log\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp[\x9f\x86\x01\x00\x90\xe4\xf1\xbbb\x8e\xf1\x07\xde\xe9\xf0\xd2\x12\xd1w\xbco\x844\x07=\x1b\xa7\x1f\xa7\x94`\x0b\xb4\x88|K')

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

    def test_2_serialize_notify_no_payload(self):

        sc = SmartContractEvent(SmartContractEvent.RUNTIME_NOTIFY, ContractParameter(ContractParameterType.Array, []), self.contract_hash, 99, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        self.assertEqual(out, b'\x1cSmartContract.Runtime.Notify\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp[c\x00\x00\x00\x90\xe4\xf1\xbbb\x8e\xf1\x07\xde\xe9\xf0\xd2\x12\xd1w\xbco\x844\x07=\x1b\xa7\x1f\xa7\x94`\x0b\xb4\x88|K')

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

    def test_2_serialize_single_notify_payload(self):

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, ContractParameter(ContractParameterType.Array, [ContractParameter(ContractParameterType.String, b'hello')]), self.contract_hash, 99, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        self.assertEqual(out, b'\x1cSmartContract.Runtime.Notify\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp[c\x00\x00\x00\x90\xe4\xf1\xbbb\x8e\xf1\x07\xde\xe9\xf0\xd2\x12\xd1w\xbco\x844\x07=\x1b\xa7\x1f\xa7\x94`\x0b\xb4\x88|K\x05hello')

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

        self.assertEqual(new_event.notify_type, b'hello')
        self.assertEqual(new_event.AddressFrom, None)
        self.assertEqual(new_event.AddressTo, None)
        self.assertEqual(new_event.Amount, 0)
        self.assertEqual(new_event.is_standard_notify, False)

    def test_3_serialize_single_transfer_notify_payload(self):

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, ContractParameter(ContractParameterType.Array, [ContractParameter(ContractParameterType.String, b'transfer')]), self.contract_hash, 99, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

        self.assertEqual(new_event.notify_type, b'transfer')
        self.assertEqual(new_event.AddressFrom, None)
        self.assertEqual(new_event.AddressTo, None)
        self.assertEqual(new_event.Amount, 0)
        self.assertEqual(new_event.is_standard_notify, False)
        self.assertEqual(new_event.ShouldPersist, False)

    def test_4_serialize_full_transfer_notify_payload(self):

        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'transfer'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.ByteArray, self.addr_from),
            ContractParameter(ContractParameterType.Integer, 123000)
        ])

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

        self.assertEqual(new_event.notify_type, b'transfer')
        self.assertEqual(new_event.AddressTo, 'ALb8FEhEmtSqv97fuNVuoLmcmrSKckffRf')
        self.assertEqual(new_event.AddressFrom, 'AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs')
        self.assertEqual(new_event.Amount, 123000)
        self.assertEqual(new_event.is_standard_notify, True)

    def test_5_serialize_full_refund_payload(self):

        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'refund'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.Integer, 123000)
        ])

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

        self.assertEqual(new_event.notify_type, b'refund')
        self.assertEqual(new_event.AddressTo, 'AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs')
        self.assertEqual(new_event.addr_from, sc.contract_hash)
        self.assertEqual(new_event.Amount, 123000)
        self.assertEqual(new_event.is_standard_notify, True)

    def test_6_serialize_full_approve_payload(self):

        payload = ContractParameter(ContractParameterType.Array, [
            ContractParameter(ContractParameterType.String, b'approve'),
            ContractParameter(ContractParameterType.ByteArray, self.addr_to),
            ContractParameter(ContractParameterType.ByteArray, self.addr_from),
            ContractParameter(ContractParameterType.ByteArray, b'x\xe0\x01')
        ])

        sc = NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload, self.contract_hash, 91349, self.event_tx, True, False)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        sc.Serialize(writer)

        out = bytes(stream.getvalue())

        StreamManager.ReleaseStream(stream)
        new_event = SmartContractEvent.FromByteArray(out)

        self.assertEqual(new_event.event_type, sc.event_type)
        self.assertEqual(new_event.contract_hash, sc.contract_hash)
        self.assertEqual(new_event.test_mode, sc.test_mode)
        self.assertEqual(new_event.tx_hash, sc.tx_hash)
        self.assertEqual(new_event.block_number, sc.block_number)

        self.assertEqual(new_event.notify_type, b'approve')
        self.assertEqual(new_event.AddressFrom, 'AKZmSGPD7ytJBbxpRPmobYGLNxdWH3Jiqs')
        self.assertEqual(new_event.AddressTo, 'ALb8FEhEmtSqv97fuNVuoLmcmrSKckffRf')
        self.assertEqual(new_event.Amount, 123000)
        self.assertEqual(new_event.is_standard_notify, True)
        self.assertEqual(new_event.ShouldPersist, True)
