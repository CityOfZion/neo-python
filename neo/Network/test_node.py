from unittest import TestCase
from neo.Network.NeoNode import NeoNode
from mock import patch
from neo.Network.Payloads.VersionPayload import VersionPayload
from neo.Network.Message import Message
from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryWriter import BinaryWriter


class Endpoint:
    def __init__(self, host, port):
        self.host = host
        self.port = port


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
