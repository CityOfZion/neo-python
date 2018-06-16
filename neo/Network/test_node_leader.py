from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Network.NodeLeader import NodeLeader
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


class Endpoint:
    def __init__(self, host, port):
        self.host = host
        self.port = port


class LeaderTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
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

        def mock_connect_tcp(host, port, factory):
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

                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST) - 1)
                        self.assertEqual(len(leader.ADDRS), len(settings.SEED_LIST) - 1)

                        # now test adding another
                        leader.RemoteNodePeerReceived('hello.com', 1234, 6)

                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

                        # now if we remove all peers, it should restart
                        peers = leader.Peers[:]
                        for peer in peers:
                            leader.RemoveConnectedPeer(peer)

                        # and peers should be equal to the seed list
                        self.assertEqual(len(leader.Peers), len(settings.SEED_LIST))

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

        def mock_connect_tcp(host, port, factory):
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
