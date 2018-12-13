from unittest import TestCase
from twisted.trial import unittest as twisted_unittest
from neo.Network.NeoNode import NeoNode
from mock import patch
from neo.Network.Payloads.VersionPayload import VersionPayload
from neo.Network.Message import Message
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Network.NodeLeader import NodeLeader
from twisted.test import proto_helpers

import sys


class Endpoint:
    def __init__(self, host, port):
        self.host = host
        self.port = port


# class NodeNetworkingTestCase(twisted_unittest.TestCase):
#     def setUp(self):
#         factory = NeoClientFactory()
#         self.proto = factory.buildProtocol(('127.0.0.1', 0))
#         self.tr = proto_helpers.StringTransport()
#         self.proto.makeConnection(self.tr)
#
#     def test_max_recursion_on_datareceived(self):
#         """
#             TDD: if the data buffer receives network data faster than it can clear it then eventually
#             `CheckDataReceived()` in `NeoNode` exceeded the max recursion depth
#         """
#         old_limit = sys.getrecursionlimit()
#         raw_message = b"\xb1\xdd\x00\x00version\x00\x00\x00\x00\x00'\x00\x00\x00a\xbb\x9av\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x0ef\x9e[mO3\xe7q\x08\x0b/NEO:2.7.4/=\x8b\x00\x00\x01"
#
#         sys.setrecursionlimit(100)
#         # we fill the buffer with 102 packets, which exceeds the 100 recursion depth limit
#         self.proto.dataReceived(raw_message * 102)
#         # no need to assert anything. If the bug still exists then we get a Python core dump and the process will stop automatically
#         # otherwise restore old limit
#         sys.setrecursionlimit(old_limit)
#
#     def tearDown(self):
#         leader = NodeLeader.Instance()
#         leader.Peers = []
#         leader.KNOWN_ADDRS = []


class NodeTestCase(TestCase):

    @patch.object(NeoNode, 'MessageReceived')
    def test_handle_message(self, mock):
        node = NeoNode()
        node.endpoint = Endpoint('hello.com', 1234)
        node.host = node.endpoint.host
        node.port = node.endpoint.port

        payload = VersionPayload(10234, 1234, 'version')

        message = Message('version', payload=payload)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)

        message.Serialize(writer)

        out = stream.getvalue()

        print("OUT %s " % out)

        out1 = out[0:10]
        out2 = out[10:20]
        out3 = out[20:]

        node.dataReceived(out1)
        node.dataReceived(out2)

        self.assertEqual(node.buffer_in, out1 + out2)
        #        import pdb
        #        pdb.set_trace()

        self.assertEqual(node.bytes_in, 20)

        mock.assert_not_called()

        node.dataReceived(out3)

        self.assertEqual(node.bytes_in, len(out))
        #        mock.assert_called_with(message)

        mock.assert_called_once()

    @patch.object(NeoNode, 'SendVersion')
    def test_data_received(self, mock):
        node = NeoNode()
        node.endpoint = Endpoint('hello.com', 1234)
        node.host = node.endpoint.host
        node.port = node.endpoint.port
        payload = VersionPayload(10234, 1234, 'version')
        message = Message('version', payload=payload)
        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        message.Serialize(writer)

        out = stream.getvalue()
        node.dataReceived(out)

        mock.assert_called_once()

        self.assertEqual(node.Version.Nonce, payload.Nonce)
