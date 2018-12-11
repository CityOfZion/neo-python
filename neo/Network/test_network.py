"""
Test handling of a node(s) disconnecting. Reasons can be:
- we shutdown node due bad responsiveness
- we shutdown node because we shutdown
- node shuts us down for unknown reason
- node shuts us down because they shutdown
"""

from twisted.trial import unittest as twisted_unittest
from twisted.internet.address import IPv4Address
from twisted.internet import error
from twisted.test import proto_helpers
from twisted.python import failure

from neo.Network.NodeLeader import NodeLeader
from neo.Network.address import Address
from neo.Network.Utils import TestTransportEndpoint
from neo.Network.NeoNode import NeoNode, HEARTBEAT_BLOCKS
from neo.Utils.NeoTestCase import NeoTestCase


class NetworkConnectionLostTests(twisted_unittest.TestCase, NeoTestCase):
    def setUp(self):
        self.node = None
        self.leader = NodeLeader.Instance()

        host, port = '127.0.0.1', 8080
        self.addr = Address(f"{host}:{port}")

        # we use a helper class such that we do not have to setup a real TCP connection
        peerAddress = IPv4Address('TCP', host, port)
        self.endpoint = TestTransportEndpoint(self.leader.reactor, str(self.addr), proto_helpers.StringTransportWithDisconnection(peerAddress=peerAddress))

        # store our deferred so we can add callbacks
        self.d = self.leader.SetupConnection(self.addr, self.endpoint)
        # make sure we create a fully running client
        self.d.addCallback(self.do_handshake)

    def tearDown(self):
        def end(err):
            self.leader.Reset()

        if self.node and self.node.connected:
            d = self.node.Disconnect()
            d.addBoth(end)
            return d
        else:
            end(None)

    def do_handshake(self, node: NeoNode):
        self.node = node
        raw_version = b"\xb1\xdd\x00\x00version\x00\x00\x00\x00\x00'\x00\x00\x00a\xbb\x9av\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x0ef\x9e[mO3\xe7q\x08\x0b/NEO:2.7.4/=\x8b\x00\x00\x01"
        raw_verack = b'\xb1\xdd\x00\x00verack\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00]\xf6\xe0\xe2'
        node.dataReceived(raw_version + raw_verack)
        return node

    def test_connection_lost_by_us(self):
        """
        Test that _we_ can force disconnect nodes and cleanup properly

        Expected behaviour:
        - added address to DEAD_ADDR list as it's unusable
        - removed address from `KNOWN_ADDR` as it's unusable
        - stopped all looping tasks of the node
        - address not in connected peers list
        """

        def should_not_happen(_):
            self.fail("Should not have been called, as our forced disconnection should call the `Errback` on the deferred")

        def conn_lost(_failure, expected_error):
            self.assertEqual(type(_failure.value), expected_error)
            self.assertIn(self.addr, self.leader.DEAD_ADDRS)
            self.assertNotIn(self.addr, self.leader.KNOWN_ADDRS)
            self.assertNotIn(self.addr, self.leader.Peers)

            node = self.endpoint.tr.protocol  # type: NeoNode
            self.assertFalse(node.has_tasks_running())

        def conn_setup(node: NeoNode):
            # at this point we should have a fully connected node, so lets try disconnecting from it
            d1 = node.Disconnect()
            d1.addCallback(should_not_happen)
            d1.addErrback(conn_lost, error.ConnectionDone)
            return d1

        self.d.addCallback(conn_setup)

        return self.d

    def test_connection_lost_normally_by_them(self):
        """
        Test handling of a normal connection lost by them (e.g. due to them shutting down)

        Expected behaviour:
        - address not in DEAD_ADDR list as it is still useable
        - address remains present in `KNOWN_ADDR` as it is still unusable
        - stopped all looping tasks of the node
        - address not in connected peers list
        """

        def conn_setup(node: NeoNode):
            # at this point we should have a fully connected node, so lets try to simulate a connection lost by the other side
            with self.assertLogHandler('network', 10) as log:
                node.connectionLost(failure.Failure(error.ConnectionDone()))

            self.assertTrue("disconnected normally with reason" in log.output[-1])
            self.assertNotIn(self.addr, self.leader.DEAD_ADDRS)
            self.assertIn(self.addr, self.leader.KNOWN_ADDRS)
            self.assertNotIn(self.addr, self.leader.Peers)

            self.assertFalse(node.has_tasks_running())

        self.d.addCallback(conn_setup)

        return self.d

    def test_connection_lost_abnormally_by_them(self):
        """
        Test handling of a connection lost by them

        Expected behaviour:
        - address not in DEAD_ADDR list as it might still be unusable
        - address present in `KNOWN_ADDR` as it might still be unusable
        - stopped all looping tasks of the node
        - address not in connected peers list
        """

        def conn_setup(node: NeoNode):
            # at this point we should have a fully connected node, so lets try to simulate a connection lost by the other side
            with self.assertLogHandler('network', 10) as log:
                node.connectionLost(failure.Failure(error.ConnectionLost()))

            self.assertIn("disconnected with connectionlost reason", log.output[-1])
            self.assertIn(str(error.ConnectionLost()), log.output[-1])
            self.assertIn("non-clean fashion", log.output[-1])

            self.assertNotIn(self.addr, self.leader.DEAD_ADDRS)
            self.assertIn(self.addr, self.leader.KNOWN_ADDRS)
            self.assertNotIn(self.addr, self.leader.Peers)

            self.assertFalse(node.has_tasks_running())

        self.d.addCallback(conn_setup)

        return self.d

    def test_connection_lost_abnormally_by_them2(self):
        """
        Test handling of 2 connection lost events within 5 minutes of each other.
        Now we can be more certain that the node is bad or doesn't want to talk to us.

        Expected behaviour:
        - address in DEAD_ADDR list as it is unusable
        - address not present in `KNOWN_ADDR` as it is unusable
        - address not in connected peers list
        - stopped all looping tasks of the node
        """

        def conn_setup(node: NeoNode):
            # at this point we should have a fully connected node, so lets try to simulate a connection lost by the other side
            with self.assertLogHandler('network', 10) as log:
                # setup last_connection, to indicate we've lost connection before
                node.address.last_connection = Address.Now()  # returns a timestamp of utcnow()

                # now lose the connection
                node.connectionLost(failure.Failure(error.ConnectionLost()))

            self.assertIn("second connection lost within 5 minutes", log.output[-1])
            self.assertIn(str(error.ConnectionLost()), log.output[-2])

            self.assertIn(self.addr, self.leader.DEAD_ADDRS)
            self.assertNotIn(self.addr, self.leader.KNOWN_ADDRS)
            self.assertNotIn(self.addr, self.leader.Peers)

            self.assertFalse(node.has_tasks_running())

        self.d.addCallback(conn_setup)

        return self.d

    def test_connection_lost_abnormally_by_them3(self):
        """
        Test for a premature disconnect

        This means the other side closes connection before the heart_beat threshold exceeded

        Expected behaviour:
        - address in DEAD_ADDR list as it is unusable
        - address not present in `KNOWN_ADDR` as it is unusable
        - address not in connected peers list
        - stopped all looping tasks of the node
        """

        def conn_setup(node: NeoNode):
            with self.assertLogHandler('network', 10) as log:
                # setup last_connection, to indicate we've lost connection before
                node.address.last_connection = Address.Now()  # returns a timestamp of utcnow()

                # setup the heartbeat data to have last happened 25 seconds ago
                # if we disconnect now we should get a premature disconnect
                node.start_outstanding_data_request[HEARTBEAT_BLOCKS] = Address.Now() - 25

                # now lose the connection
                node.connectionLost(failure.Failure(error.ConnectionLost()))

            self.assertIn("Premature disconnect", log.output[-2])
            self.assertIn(str(error.ConnectionLost()), log.output[-1])

            self.assertIn(self.addr, self.leader.DEAD_ADDRS)
            self.assertNotIn(self.addr, self.leader.KNOWN_ADDRS)
            self.assertNotIn(self.addr, self.leader.Peers)

            self.assertFalse(node.has_tasks_running())

        self.d.addCallback(conn_setup)

        return self.d
