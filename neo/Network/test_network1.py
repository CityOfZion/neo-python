"""
Test Nodeleader basics: starting and stopping

"""

from neo.Network.NodeLeader import NodeLeader
from neo.Network.address import Address
from twisted.trial import unittest as twisted_unittest
from twisted.internet import reactor as twisted_reactor
from twisted.internet import error
from mock import MagicMock


class NetworkBasicTest(twisted_unittest.TestCase):
    def tearDown(self):
        NodeLeader.Reset()

    def test_nodeleader_start_stop(self):
        orig_connectTCP = twisted_reactor.connectTCP
        twisted_reactor.connectTCP = MagicMock()

        seed_list = ['127.0.0.1:80', '127.0.0.2:80']
        leader = NodeLeader.Instance(reactor=twisted_reactor)

        leader.Start(seed_list=seed_list)
        self.assertEqual(twisted_reactor.connectTCP.call_count, 2)
        self.assertEqual(len(leader.KNOWN_ADDRS), 2)

        for seed, call in zip(seed_list, twisted_reactor.connectTCP.call_args_list):
            host, port = seed.split(':')
            arg = call[0]

            self.assertEqual(arg[0], host)
            self.assertEqual(arg[1], int(port))

        self.assertTrue(leader.peer_check_loop.running)
        self.assertTrue(leader.blockheight_loop.running)
        self.assertTrue(leader.memcheck_loop.running)

        leader.Shutdown()

        self.assertFalse(leader.peer_check_loop.running)
        self.assertFalse(leader.blockheight_loop.running)
        self.assertFalse(leader.memcheck_loop.running)

        # cleanup
        twisted_reactor.connectTCP = orig_connectTCP

    def test_nodeleader_start_skip_seeds(self):
        orig_connectTCP = twisted_reactor.connectTCP
        twisted_reactor.connectTCP = MagicMock()

        seed_list = ['127.0.0.1:80', '127.0.0.2:80']
        leader = NodeLeader(reactor=twisted_reactor)

        leader.Start(seed_list=seed_list, skip_seeds=True)

        self.assertEqual(twisted_reactor.connectTCP.call_count, 0)
        self.assertEqual(len(leader.KNOWN_ADDRS), 0)

        self.assertTrue(leader.peer_check_loop.running)
        self.assertTrue(leader.blockheight_loop.running)
        self.assertTrue(leader.memcheck_loop.running)

        leader.Shutdown()

        # cleanup
        twisted_reactor.connectTCP = orig_connectTCP

    def test_connection_refused(self):
        """Test handling of a bad address. Where bad could be a dead or unreachable endpoint

        Expected behaviour:
            - add address to DEAD_ADDR list as it's unusable
            - remove address from KNOWN_ADDR list as it's unusable
        """
        leader = NodeLeader.Instance()

        PORT_WITH_NO_SERVICE = 12312
        addr = Address("127.0.0.1:" + str(PORT_WITH_NO_SERVICE))

        # normally this is done by NodeLeader.Start(), now we add the address manually so we can verify it's removed properly
        leader.KNOWN_ADDRS.append(addr)

        def connection_result(value):
            self.assertEqual(error.ConnectionRefusedError, value)
            self.assertIn(addr, leader.DEAD_ADDRS)
            self.assertNotIn(addr, leader.KNOWN_ADDRS)

        d = leader.SetupConnection(addr)  # type: Deferred
        # leader.clientConnectionFailed() does not rethrow the Failure, therefore we should get the result via the callback, not errback.
        # adding both for simplicity. The test will fail on the first assert if the connection was successful.
        d.addBoth(connection_result)

        return d
