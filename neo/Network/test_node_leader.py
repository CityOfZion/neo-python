from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Network.NodeLeader import NodeLeader, NeoClientFactory
from neo.Network.NeoNode import NeoNode
from mock import patch
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Core.TX.Transaction import ContractTransaction, TransactionOutput
from neo.Core.TX.MinerTransaction import MinerTransaction
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.address import IPv4Address
from mock import MagicMock
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi


class Endpoint:
    def __init__(self, host, port):
        self.host = host
        self.port = port


class NodeLeaderConnectionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # clean up left over of other tests classes
        leader = NodeLeader.Instance()
        leader.Peers = []
        leader.ADDRS = []

    def _add_new_node(self, host, port):
        self.tr.getPeer.side_effect = [IPv4Address('TCP', host, port)]
        node = self.factory.buildProtocol(('127.0.0.1', 0))
        node.makeConnection(self.tr)

        return node

    def setUp(self):
        self.factory = NeoClientFactory()
        self.tr = proto_helpers.StringTransport()
        self.tr.getPeer = MagicMock()
        self.leader = NodeLeader.Instance()

    def test_getpeer_list_vs_maxpeer_list(self):
        """https://github.com/CityOfZion/neo-python/issues/678"""
        settings.set_max_peers(1)
        api_server = JsonRpcApi(None, None)
        # test we start with a clean state
        peers = api_server.get_peers()
        self.assertEqual(len(peers['connected']), 0)

        # try connecting more nodes than allowed by the max peers settings
        first_node = self._add_new_node('127.0.0.1', 1111)
        second_node = self._add_new_node('127.0.0.2', 2222)
        peers = api_server.get_peers()
        # should respect max peer setting
        self.assertEqual(1, len(peers['connected']))
        self.assertEqual('127.0.0.1', peers['connected'][0]['address'])
        self.assertEqual(1111, peers['connected'][0]['port'])

        # now drop the existing node
        self.factory.clientConnectionLost(first_node, reason="unittest")
        # add a new one
        second_node = self._add_new_node('127.0.0.2', 2222)
        # and test if `first_node` we dropped can pass limit checks when it reconnects
        self.leader.PeerCheckLoop()
        peers = api_server.get_peers()
        self.assertEqual(1, len(peers['connected']))
        self.assertEqual('127.0.0.2', peers['connected'][0]['address'])
        self.assertEqual(2222, peers['connected'][0]['port'])

        # restore default settings
        settings.set_max_peers(5)


class LeaderTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(LeaderTestCase.wallet_1_dest(), to_aes_key(LeaderTestCase.wallet_1_pass()))
        return cls._wallet1

    @classmethod
    def tearDown(self):
        NodeLeader.Instance().Peers = []
        NodeLeader.__LEAD = None

    def test_initialize(self):
        leader = NodeLeader.Instance()
        self.assertEqual(leader.Peers, [])
        self.assertEqual(leader.ADDRS, [])
        self.assertEqual(leader.UnconnectedPeers, [])

    def test_peer_adding(self):
        leader = NodeLeader.Instance()
        Blockchain.Default()._block_cache = {'hello': 1}

        def mock_call_later(delay, method, *args):
            method(*args)

        def mock_connect_tcp(host, port, factory, timeout=120):
            node = NeoNode()
            node.endpoint = Endpoint(host, port)
            leader.AddConnectedPeer(node)
            return node

        def mock_disconnect(peer):
            return True

        def mock_send_msg(node, message):
            return True

        settings.set_max_peers(len(settings.SEED_LIST))

        with patch('twisted.internet.reactor.connectTCP', mock_connect_tcp):
            with patch('twisted.internet.reactor.callLater', mock_call_later):
                with patch('neo.Network.NeoNode.NeoNode.Disconnect', mock_disconnect):
                    with patch('neo.Network.NeoNode.NeoNode.SendSerializedMessage', mock_send_msg):
                        leader.Start()
                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

                        # now test adding another
                        leader.RemoteNodePeerReceived('hello.com', 1234, 6)

                        # it shouldnt add anything so it doesnt go over max connected peers
                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

                        # test adding peer
                        peer = NeoNode()
                        peer.endpoint = Endpoint('hellloo.com', 12344)
                        leader.ADDRS.append('hellloo.com:12344')
                        leader.AddConnectedPeer(peer)
                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

                        # now get a peer
                        peer = leader.Peers[0]

                        leader.RemoveConnectedPeer(peer)

                        # the connect peers should be 1 less than the seed_list
                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST) - 1)
                        # the known addresses should be equal the seed_list
                        self.assertEqual(len(leader.ADDRS), len(settings.SEED_LIST))

                        # now test adding another
                        leader.RemoteNodePeerReceived('hello.com', 1234, 6)

                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

                        # now if we remove all peers, it should restart
                        peers = leader.Peers[:]
                        for peer in peers:
                            leader.RemoveConnectedPeer(peer)

                        # test reset
                        leader.ResetBlockRequestsAndCache()
                        self.assertEqual(Blockchain.Default()._block_cache, {})

    def _generate_tx(self):
        wallet = self.GetWallet1()

        output = TransactionOutput(AssetId=Blockchain.SystemShare().Hash, Value=Fixed8.One(),
                                   script_hash=LeaderTestCase.wallet_1_script_hash)
        contract_tx = ContractTransaction(outputs=[output])
        wallet.MakeTransaction(contract_tx)
        ctx = ContractParametersContext(contract_tx)
        wallet.Sign(ctx)
        contract_tx.scripts = ctx.GetScripts()
        return contract_tx

    def test_relay(self):
        leader = NodeLeader.Instance()

        def mock_call_later(delay, method, *args):
            method(*args)

        def mock_connect_tcp(host, port, factory, timeout=120):
            node = NeoNode()
            node.endpoint = Endpoint(host, port)
            leader.AddConnectedPeer(node)
            return node

        def mock_send_msg(node, message):
            return True

        with patch('twisted.internet.reactor.connectTCP', mock_connect_tcp):
            with patch('twisted.internet.reactor.callLater', mock_call_later):
                with patch('neo.Network.NeoNode.NeoNode.SendSerializedMessage', mock_send_msg):
                    leader.Start()

                    miner = MinerTransaction()

                    res = leader.Relay(miner)
                    self.assertFalse(res)

                    tx = self._generate_tx()

                    res = leader.Relay(tx)
                    self.assertEqual(res, True)

                    self.assertTrue(tx.Hash.ToBytes() in leader.MemPool.keys())
                    res2 = leader.Relay(tx)
                    self.assertFalse(res2)

    def test_inventory_received(self):

        leader = NodeLeader.Instance()

        miner = MinerTransaction()
        miner.Nonce = 1234
        res = leader.InventoryReceived(miner)

        self.assertFalse(res)

        block = Blockchain.Default().GenesisBlock()

        res2 = leader.InventoryReceived(block)

        self.assertFalse(res2)

        tx = self._generate_tx()

        res = leader.InventoryReceived(tx)

        self.assertIsNone(res)
