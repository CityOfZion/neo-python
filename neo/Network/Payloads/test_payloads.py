
from .VersionPayload import VersionPayload
from neo.Network.Message import Message
from neo.IO.Helper import AsSerializableWithType
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
from neo import Settings
from neo.Core.Helper import Helper
import random
import unittest
import binascii


class PayloadTestCase(unittest.TestCase):

    port = 20333
    nonce = random.randint(12949672,42949672)
    ua = "NEO Python v0.01"

    payload = None
    def setUp(self):


        self.payload = VersionPayload(self.port, self.nonce, self.ua)

    def test_aversion_create(self):

        self.assertEqual(self.payload.Nonce, self.nonce)
        self.assertEqual(self.payload.Port, self.port)
        self.assertEqual(self.payload.UserAgent, self.ua)


    def test_aversion_serialization(self):

        serialized = binascii.unhexlify( Helper.ToArray(self.payload))

        deserialized_version = AsSerializableWithType(serialized, 'neo.Network.Payloads.VersionPayload.VersionPayload')

        v = deserialized_version

        self.assertEqual(v.Nonce, self.nonce)
        self.assertEqual(v.Port, self.port)
        self.assertEqual(v.UserAgent, self.ua)
        self.assertEqual(v.Timestamp, self.payload.Timestamp)
        self.assertEqual(v.StartHeight, self.payload.StartHeight)
        self.assertEqual(v.Version, self.payload.Version)
        self.assertEqual(v.Services, self.payload.Services)
        self.assertEqual(v.Relay, self.payload.Relay)


    def test_message_serialization(self):

        message = Message('version', payload=self.payload)

        self.assertEqual(message.Command, 'version')

        ms = MemoryStream()
        writer = BinaryWriter(ms)

        message.Serialize(writer)

        result = binascii.unhexlify( ms.ToArray())

        ms = MemoryStream(result)
        reader = BinaryReader(ms)

        deserialized_message = Message()
        deserialized_message.Deserialize( reader )

        dm = deserialized_message

        self.assertEqual(dm.Command, 'version')

        self.assertEqual(dm.Magic, Settings.MAGIC)

        checksum = Message.GetChecksum(dm.Payload)

        self.assertEqual(checksum, dm.Checksum)


        deserialized_version = AsSerializableWithType(dm.Payload, 'neo.Network.Payloads.VersionPayload.VersionPayload')


        self.assertEqual(deserialized_version.Port, self.port)
        self.assertEqual(deserialized_version.UserAgent, self.ua)

        self.assertEqual(deserialized_version.Timestamp, self.payload.Timestamp)