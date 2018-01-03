import random
import binascii
from datetime import datetime

from neo.Utils.NeoTestCase import NeoTestCase
from neo.Network.Payloads.VersionPayload import VersionPayload
from neo.Network.Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from neo.Network.Message import Message
from neo.IO.Helper import Helper as IOHelper
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.Settings import settings
from neo.Core.Helper import Helper


class PayloadTestCase(NeoTestCase):

    port = 20333
    nonce = random.randint(12949672, 42949672)
    ua = "/NEO:2.4.1/"

    payload = None

    def setUp(self):

        self.payload = VersionPayload(self.port, self.nonce, self.ua)

    def test_version_create(self):

        self.assertEqual(self.payload.Nonce, self.nonce)
        self.assertEqual(self.payload.Port, self.port)
        self.assertEqual(self.payload.UserAgent, self.ua)

    def test_version_serialization(self):

        serialized = binascii.unhexlify(Helper.ToArray(self.payload))

        deserialized_version = IOHelper.AsSerializableWithType(serialized, 'neo.Network.Payloads.VersionPayload.VersionPayload')

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

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        message.Serialize(writer)

        result = binascii.unhexlify(ms.ToArray())
        StreamManager.ReleaseStream(ms)

        ms = StreamManager.GetStream(result)
        reader = BinaryReader(ms)

        deserialized_message = Message()
        deserialized_message.Deserialize(reader)

        StreamManager.ReleaseStream(ms)

        dm = deserialized_message

        self.assertEqual(dm.Command, 'version')

        self.assertEqual(dm.Magic, settings.MAGIC)

        checksum = Message.GetChecksum(dm.Payload)

        self.assertEqual(checksum, dm.Checksum)

        deserialized_version = IOHelper.AsSerializableWithType(dm.Payload, 'neo.Network.Payloads.VersionPayload.VersionPayload')

        self.assertEqual(deserialized_version.Port, self.port)
        self.assertEqual(deserialized_version.UserAgent, self.ua)

        self.assertEqual(deserialized_version.Timestamp, self.payload.Timestamp)

    def test_network_addrtime(self):

        addr = "55.15.69.104"
        port = 10333
        ts = int(datetime.now().timestamp())
        services = 0

        nawt = NetworkAddressWithTime(addr, port, services, ts)

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        nawt.Serialize(writer)

        arr = ms.ToArray()
        arhex = binascii.unhexlify(arr)

        StreamManager.ReleaseStream(ms)

        ms = StreamManager.GetStream(arhex)
        reader = BinaryReader(ms)

        nawt2 = NetworkAddressWithTime()
        nawt2.Deserialize(reader)

        StreamManager.ReleaseStream(ms)

#        self.assertEqual(nawt.Address, nawt2.Address)
        self.assertEqual(nawt.Services, nawt2.Services)
        self.assertEqual(nawt.Port, nawt2.Port)
        self.assertEqual(nawt.Timestamp, nawt2.Timestamp)
