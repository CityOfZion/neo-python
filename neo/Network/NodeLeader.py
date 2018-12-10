import random
import time
from typing import List
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode, HEARTBEAT_BLOCKS
from neo.Settings import settings
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import error
from twisted.internet import task
from twisted.internet import reactor as twisted_reactor
from twisted.internet.defer import CancelledError, Deferred
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from neo.logging import log_manager
from neo.Network.address import Address
from neo.Network.Utils import LoopingCall

logger = log_manager.getLogger('network')
log_manager.config_stdio([('network', 10)])


class NodeLeader:
    _LEAD = None

    Peers = []

    KNOWN_ADDRS = []
    DEAD_ADDRS = []

    NodeId = None

    _MissedBlocks = []

    BREQPART = 100
    BREQMAX = 10000

    KnownHashes = []
    MissionsGlobal = []
    MemPool = {}
    RelayCache = {}

    NodeCount = 0

    CurrentBlockheight = 0

    ServiceEnabled = False

    peer_check_loop = None
    peer_check_loop_deferred = None

    check_bcr_loop = None
    check_bcr_loop_deferred = None

    memcheck_loop = None
    memcheck_loop_deferred = None

    blockheight_loop = None
    blockheight_loop_deferred = None

    task_handles = {}

    @staticmethod
    def Instance(reactor=None):
        """
        Get the local node instance.

        Args:
            reactor: (optional) custom reactor to use in NodeLeader.

        Returns:
            NodeLeader: instance.
        """
        if NodeLeader._LEAD is None:
            NodeLeader._LEAD = NodeLeader(reactor)
        return NodeLeader._LEAD

    def __init__(self, reactor=None):
        """
        Create an instance.
        This is the equivalent to C#'s LocalNode.cs
        """
        self.Setup()
        self.ServiceEnabled = settings.SERVICE_ENABLED
        self.peer_zero_count = 0  # track the number of times PeerCheckLoop saw a Peer count of zero. Reset e.g. after 3 times
        self.connection_queue = []
        self.reactor = twisted_reactor

        self.forced_disconnect_by_us = 0

        # for testability
        if reactor:
            self.reactor = reactor

    def start_peer_check_loop(self):
        logger.debug(f"start_peer_check_loop")
        if self.peer_check_loop and self.peer_check_loop.running:
            logger.debug("start_peer_check_loop: still running -> stopping...")
            self.stop_peer_check_loop()

        self.peer_check_loop = LoopingCall(self.PeerCheckLoop, clock=self.reactor)
        self.peer_check_loop_deferred = self.peer_check_loop.start(10, now=False)
        self.peer_check_loop_deferred.addErrback(self.OnPeerLoopError)

    def stop_peer_check_loop(self, cancel=True):
        logger.debug(f"stop_peer_check_loop, cancel: {cancel}")
        if self.peer_check_loop and self.peer_check_loop.running:
            logger.debug(f"stop_peer_check_loop, calling stop()")
            self.peer_check_loop.stop()
        if cancel and self.peer_check_loop_deferred:
            logger.debug(f"stop_peer_check_loop, calling cancel()")
            self.peer_check_loop_deferred.cancel()

    def start_check_bcr_loop(self):
        logger.debug(f"start_check_bcr_loop")
        if self.check_bcr_loop and self.check_bcr_loop.running:
            logger.debug("start_check_bcr_loop: still running -> stopping...")
            self.stop_check_bcr_loop()

        self.check_bcr_loop = LoopingCall(self.check_bcr_catchup, clock=self.reactor)
        self.check_bcr_loop_deferred = self.check_bcr_loop.start(5)
        self.check_bcr_loop_deferred.addErrback(self.OnCheckBcrError)

    def stop_check_bcr_loop(self, cancel=True):
        logger.debug(f"stop_check_bcr_loop, cancel: {cancel}")
        if self.check_bcr_loop and self.check_bcr_loop.running:
            logger.debug(f"stop_check_bcr_loop, calling stop()")
            self.check_bcr_loop.stop()
        if cancel and self.check_bcr_loop_deferred:
            logger.debug(f"stop_check_bcr_loop, calling cancel()")
            self.check_bcr_loop_deferred.cancel()

    def start_memcheck_loop(self):
        self.stop_memcheck_loop()
        self.memcheck_loop = LoopingCall(self.MempoolCheck, clock=self.reactor)
        self.memcheck_loop_deferred = self.memcheck_loop.start(240, now=False)
        self.memcheck_loop_deferred.addErrback(self.OnMemcheckError)

    def stop_memcheck_loop(self, cancel=True):
        if self.memcheck_loop and self.memcheck_loop.running:
            self.memcheck_loop.stop()
        if cancel and self.memcheck_loop_deferred:
            self.memcheck_loop_deferred.cancel()

    def start_blockheight_loop(self):
        self.stop_blockheight_loop()
        self.CurrentBlockheight = BC.Default().Height
        self.blockheight_loop = LoopingCall(self.BlockheightCheck, clock=self.reactor)
        self.blockheight_loop_deferred = self.blockheight_loop.start(240, now=False)
        self.blockheight_loop_deferred.addErrback(self.OnBlockheightcheckError)

    def stop_blockheight_loop(self, cancel=True):
        if self.blockheight_loop and self.blockheight_loop.running:
            self.blockheight_loop.stop()
        if cancel and self.blockheight_loop_deferred:
            self.blockheight_loop_deferred.cancel()

    def Setup(self):
        """
        Initialize the local node.

        Returns:

        """
        self.Peers = []  # active nodes that we're connected to
        self.KNOWN_ADDRS = []  # node addresses that we've learned about from other nodes
        self.DEAD_ADDRS = []  # addresses that were performing poorly or we could not establish a connection to
        self.MissionsGlobal = []
        self.NodeId = random.randint(1294967200, 4294967200)

    def Restart(self):
        self.stop_peer_check_loop()
        self.stop_check_bcr_loop()
        self.stop_memcheck_loop()
        self.stop_blockheight_loop()

        self.peer_check_loop_deferred = None
        self.check_bcr_loop_deferred = None
        self.memcheck_loop_deferred = None
        self.blockheight_loop_deferred = None

        if len(self.Peers) == 0:
            # preserve any addresses we know because the peers in the seedlist might have gone bad and then we can't receive new addresses anymore
            unique_addresses = list(set(self.KNOWN_ADDRS + self.DEAD_ADDRS))
            self.KNOWN_ADDRS = unique_addresses
            self.DEAD_ADDRS = []
            self.peer_zero_count = 0
            self.connection_queue = []

            self.Start(skip_seeds=True)

    def throttle_sync(self):
        for peer in self.Peers:  # type: NeoNode
            peer.stop_block_loop(cancel=False)
            peer.stop_peerinfo_loop(cancel=False)
            peer.stop_header_loop(cancel=False)

        # start a loop to check if we've caught up on our requests
        if not self.check_bcr_loop:
            self.start_check_bcr_loop()

    def check_bcr_catchup(self):
        """we're exceeding data request speed vs receive + process"""
        logger.debug(f"Checking if BlockRequests has caught up {len(BC.Default().BlockRequests)}")

        # test, perhaps there's some race condition between slow startup and throttle sync, otherwise blocks will never go down
        for peer in self.Peers:  # type: NeoNode
            peer.stop_block_loop(cancel=False)
            peer.stop_peerinfo_loop(cancel=False)
            peer.stop_header_loop(cancel=False)

        if len(BC.Default().BlockRequests) > 0:
            for peer in self.Peers:
                peer.keep_alive()
                peer.health_check(HEARTBEAT_BLOCKS)
                peer_bcr_len = len(peer.myblockrequests)
                # if a peer has cleared its queue then reset heartbeat status to avoid timing out when resuming from "check_bcr" if there's 1 or more really slow peer(s)
                if peer_bcr_len == 0:
                    peer.start_outstanding_data_request[HEARTBEAT_BLOCKS] = 0

                print(f"{peer.prefix} request count: {peer_bcr_len}")
                if peer_bcr_len == 1:
                    next_hash = BC.Default().GetHeaderHash(self.CurrentBlockheight + 1)
                    print(f"{peer.prefix} {peer.myblockrequests} {next_hash}")
        else:
            # we're done catching up. Stop own loop and restart peers
            self.stop_check_bcr_loop()
            self.check_bcr_loop = None
            logger.debug("BlockRequests have caught up...resuming sync")
            for peer in self.Peers:
                peer.ProtocolReady()  # this starts all loops again
                # give a little bit of time between startup of peers
                time.sleep(2)

    def _process_connection_queue(self):
        for addr in self.connection_queue:
            # check that we're not already in the process of trying to connect (some connections take long to setup, we don't want to double queue)
            if not addr.is_connecting:
                addr.is_connecting = True
                self.SetupConnection(addr)

    def Start(self, seed_list: List[str] = None, skip_seeds: bool = False) -> None:
        """
        Start connecting to the seed list.

        Args:
            seed_list: a list of host:port strings if not supplied use list from `protocol.xxx.json`
            skip_seeds: skip connecting to seed list
        """
        if not seed_list:
            seed_list = settings.SEED_LIST

        logger.debug("Starting up nodeleader")
        if not skip_seeds:
            logger.debug("Attempting to connect to seed list...")
            for bootstrap in seed_list:
                addr = Address(bootstrap)
                self.KNOWN_ADDRS.append(addr)
                # host, port = bootstrap.split(":")
                # self.SetupConnection(host, port)
                self.SetupConnection(addr)

        logger.debug("Starting up nodeleader: starting peer, mempool, and blockheight check loops")
        # check in on peers every 10 seconds
        self.start_peer_check_loop()
        self.start_memcheck_loop()
        self.start_blockheight_loop()

        # TODO: change to new endpoint api
        # if settings.ACCEPT_INCOMING_PEERS:
        #     logger.debug(f"Starting up nodeleader: setting up listen server on port: '{settings.NODE_PORT}")
        #     # TODO: add address to known KNOWN_ADDR list, change to use endpoint instead
        #     self.reactor.listenTCP(settings.NODE_PORT, NeoClientFactory(incoming_client=True))

    def setBlockReqSizeAndMax(self, breqpart=0, breqmax=0):
        if breqpart > 0 and breqmax > 0 and breqmax > breqpart:
            self.BREQPART = breqpart
            self.BREQMAX = breqmax
            logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (
                self.BREQPART, self.BREQMAX))
        else:
            logger.info(
                "invalid values. Please specify a block request part and max size for each node, like 30 and 1000")

    def setBlockReqSizeByName(self, name):
        if name.lower() == 'slow':
            self.BREQPART = 15
            self.BREQMAX = 5000
        elif name.lower() == 'normal':
            self.BREQPART = 100
            self.BREQMAX = 10000
        elif name.lower() == 'fast':
            self.BREQPART = 250
            self.BREQMAX = 15000
        else:
            logger.info("configuration name %s not found. use 'slow', 'normal', or 'fast'" % name)

        logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (
            self.BREQPART, self.BREQMAX))

    def RemoteNodePeerReceived(self, host, port, via_node_addr):
        addr = Address("%s:%s" % (host, port))
        if addr not in self.KNOWN_ADDRS and addr not in self.DEAD_ADDRS:
            logger.debug(f"Adding new address {addr:>21} to known addresses list, received from {via_node_addr}")
            # we always want to save new addresses in case we lose all active connections before we can request a new list
            self.KNOWN_ADDRS.append(addr)

    def SetupConnection(self, addr, endpoint=None):
        if len(self.Peers) < settings.CONNECTED_PEER_MAX:
            try:
                host, port = addr.split(':')
                # self.reactor.connectTCP(host, int(port), NeoClientFactory(), timeout=120)
                if endpoint:
                    point = endpoint
                else:
                    point = TCP4ClientEndpoint(self.reactor, host, int(port))
                d = connectProtocol(point, NeoNode())  # type: Deferred
                d.addErrback(self.clientConnectionFailed, addr)
                return d
            except Exception as e:
                logger.error(f"Setup connection with with {e}")

    def Shutdown(self):
        """Disconnect all connected peers."""
        logger.debug("Nodeleader shutting down")

        self.stop_peer_check_loop()
        self.peer_check_loop_deferred = None

        self.stop_check_bcr_loop()
        self.check_bcr_loop_deferred = None

        self.stop_memcheck_loop()
        self.memcheck_loop_deferred = None

        self.stop_blockheight_loop()
        self.blockheight_loop_deferred = None

        for p in self.Peers:
            p.Disconnect()

    def AddConnectedPeer(self, peer):
        """
        Add a new connect peer to the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        # if present
        self.RemoveFromQueue(peer.address)

        if peer not in self.Peers and len(self.Peers) < settings.CONNECTED_PEER_MAX:
            self.Peers.append(peer)
            self.AddKnownAddress(peer.address)
        else:
            # either peer is already in the list and it has reconnected before it timed out on our side
            # or it's trying to connect multiple times
            # or we hit the max connected peer count
            self.RemoveKnownAddress(peer.address)
            peer.Disconnect()

    def RemoveConnectedPeer(self, peer):
        """
        Remove a connected peer from the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        if peer in self.Peers:
            self.Peers.remove(peer)

    def RemoveFromQueue(self, addr):
        """
        Remove an address from the connection queue
        Args:
            addr:

        Returns:

        """
        if addr in self.connection_queue:
            self.connection_queue.remove(addr)

    def RemoveKnownAddress(self, addr):
        if addr in self.KNOWN_ADDRS:
            self.KNOWN_ADDRS.remove(addr)

    def AddKnownAddress(self, addr):
        if addr not in self.KNOWN_ADDRS:
            self.KNOWN_ADDRS.append(addr)

    def AddDeadAddress(self, addr, reason=None):
        if addr not in self.DEAD_ADDRS:
            if reason:
                logger.debug(f"Adding address {addr:>21} to DEAD_ADDRS list. Reason: {reason}")
            else:
                logger.debug(f"Adding address {addr:>21} to DEAD_ADDRS list.")
            self.DEAD_ADDRS.append(addr)

        # something in the dead_addrs list cannot be in the known_addrs list. Which holds either "tested and good" or "untested" addresses
        self.RemoveKnownAddress(addr)

    def OnSetupConnectionErr(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("On setup connection error! %s" % err)

    def OnCheckBcrError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("On Check BlockRequest error! %s" % err)

    def OnPeerLoopError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Peer check loop %s " % err)

    def OnMemcheckError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Memcheck check %s " % err)

    def OnBlockheightcheckError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Blockheight check loop %s " % err)

    def PeerCheckLoop(self):
        # often times things will get stuck on 1 peer so
        # every so often we will try to reconnect to peers
        # that were previously active but lost their connection
        logger.debug(
            f"Peer check loop...checking [A:{len(self.KNOWN_ADDRS)} D:{len(self.DEAD_ADDRS)} C:{len(self.Peers)} M:{settings.CONNECTED_PEER_MAX} "
            f"Q:{len(self.connection_queue)}]")

        connected = []
        peer_to_remove = []

        for peer in self.Peers:
            if peer.endpoint == "":
                peer_to_remove.append(peer)
            else:
                connected.append(peer.address)
        for p in peer_to_remove:
            self.Peers.remove(p)

        self._ensure_peer_tasks_running(connected)
        self._check_for_queuing_possibilities(connected)
        self._process_connection_queue()
        # keep this last, to ensure we first try queueing.
        self._monitor_for_zero_connected_peers()

    def _check_for_queuing_possibilities(self, connected):
        # we sort addresses such that those that we recently disconnected from are last in the list
        self.KNOWN_ADDRS.sort(key=lambda address: address.last_connection)
        to_remove = []
        for addr in self.KNOWN_ADDRS:
            if addr in self.DEAD_ADDRS:
                logger.debug(f"Address {addr} found in DEAD_ADDRS list...skipping")
                to_remove.append(addr)
                continue
            if addr not in connected and addr not in self.connection_queue and len(self.Peers) + len(
                    self.connection_queue) < settings.CONNECTED_PEER_MAX:
                self.connection_queue.append(addr)
                logger.debug(
                    f"Queuing {addr:>21} for new connection [in queue: {len(self.connection_queue)} "
                    f"connected: {len(self.Peers)} maxpeers:{settings.CONNECTED_PEER_MAX}]")

        # we couldn't remove addresses found in the DEAD_ADDR list from ADDRS while looping over it
        # so we do it now to clean up
        for addr in to_remove:
            # TODO: might be able to remove. Check if this scenario is still possible since the refactor
            try:
                self.KNOWN_ADDRS.remove(addr)
            except KeyError:
                pass

    def _monitor_for_zero_connected_peers(self):
        """
        Track if we lost connection to all peers.
        Give some retries threshold to allow peers that are in the process of connecting or in the queue to be connected to run

        """
        if len(self.Peers) == 0 and len(self.connection_queue) == 0:
            if self.peer_zero_count > 2:
                logger.debug("Peer count 0 exceeded max retries threshold, restarting...")
                self.Restart()
            else:
                logger.debug(
                    f"Peer count is 0, allow for retries or queued connections to be established {self.peer_zero_count}")
                self.peer_zero_count += 1

    def _ensure_peer_tasks_running(self, connected):
        # double check that the peers that are connected are running their tasks
        # unless we're data throttling
        # there has been a case where the connection was established, but ProtocolReady() never called nor disconnected.
        if not self.check_bcr_loop:
            for peer in self.Peers:
                if not peer.has_tasks_running:
                    peer.start_all_tasks()

    def InventoryReceived(self, inventory):
        """
        Process a received inventory.

        Args:
            inventory (neo.Network.Inventory): expect a Block type.

        Returns:
            bool: True if processed and verified. False otherwise.
        """
        if inventory.Hash.ToBytes() in self._MissedBlocks:
            self._MissedBlocks.remove(inventory.Hash.ToBytes())

        if inventory is MinerTransaction:
            return False

        if type(inventory) is Block:
            if BC.Default() is None:
                return False

            if BC.Default().ContainsBlock(inventory.Index):
                return False

            if not BC.Default().AddBlock(inventory):
                return False

        else:
            if not inventory.Verify(self.MemPool.values()):
                return False

    def RelayDirectly(self, inventory):
        """
        Relay the inventory to the remote client.

        Args:
            inventory (neo.Network.Inventory):

        Returns:
            bool: True if relayed successfully. False otherwise.
        """
        relayed = False

        self.RelayCache[inventory.Hash.ToBytes()] = inventory

        for peer in self.Peers:
            relayed |= peer.Relay(inventory)

        if len(self.Peers) == 0:
            if type(BC.Default()) is TestLevelDBBlockchain:
                # mock a true result for tests
                return True

            logger.info("no connected peers")

        return relayed

    def Relay(self, inventory):
        """
        Relay the inventory to the remote client.

        Args:
            inventory (neo.Network.Inventory):

        Returns:
            bool: True if relayed successfully. False otherwise.
        """
        if type(inventory) is MinerTransaction:
            return False

        if inventory.Hash.ToBytes() in self.KnownHashes:
            return False

        self.KnownHashes.append(inventory.Hash.ToBytes())

        if type(inventory) is Block:
            pass

        elif type(inventory) is Transaction or issubclass(type(inventory), Transaction):
            if not self.AddTransaction(inventory):
                # if we fail to add the transaction for whatever reason, remove it from the known hashes list or we cannot retry the same transaction again
                try:
                    self.KnownHashes.remove(inventory.Hash.ToBytes())
                except ValueError:
                    # it not found
                    pass
                return False
        else:
            # consensus
            pass

        relayed = self.RelayDirectly(inventory)
        return relayed

    def GetTransaction(self, hash):
        if hash in self.MemPool.keys():
            return self.MemPool[hash]
        return None

    def AddTransaction(self, tx):
        """
        Add a transaction to the memory pool.

        Args:
            tx (neo.Core.TX.Transaction): instance.

        Returns:
            bool: True if successfully added. False otherwise.
        """
        if BC.Default() is None:
            return False

        if tx.Hash.ToBytes() in self.MemPool.keys():
            return False

        if BC.Default().ContainsTransaction(tx.Hash):
            return False

        if not tx.Verify(self.MemPool.values()):
            logger.error("Verifying tx result... failed")
            return False

        self.MemPool[tx.Hash.ToBytes()] = tx

        return True

    def RemoveTransaction(self, tx):
        """
        Remove a transaction from the memory pool if it is found on the blockchain.

        Args:
            tx (neo.Core.TX.Transaction): instance.

        Returns:
            bool: True if successfully removed. False otherwise.
        """
        if BC.Default() is None:
            return False

        if not BC.Default().ContainsTransaction(tx.Hash):
            return False

        if tx.Hash.ToBytes() in self.MemPool:
            del self.MemPool[tx.Hash.ToBytes()]
            return True

        return False

    def MempoolCheck(self):
        """
        Checks the Mempool and removes any tx found on the Blockchain
        Implemented to resolve https://github.com/CityOfZion/neo-python/issues/703
        """
        txs = []
        values = self.MemPool.values()
        for tx in values:
            txs.append(tx)

        for tx in txs:
            res = self.RemoveTransaction(tx)
            if res:
                logger.debug("found tx 0x%s on the blockchain ...removed from mempool" % tx.Hash)

    def BlockheightCheck(self):
        """
        Checks the current blockheight and finds the peer that prevents advancement
        """
        if self.CurrentBlockheight == BC.Default().Height:
            logger.debug("Blockheight is not advancing ...")
            next_hash = BC.Default().GetHeaderHash(self.CurrentBlockheight + 1)
            for peer in self.Peers:
                if next_hash in peer.myblockrequests:
                    peer.Disconnect()
                    break
        else:
            self.CurrentBlockheight = BC.Default().Height

    def clientConnectionFailed(self, err, address: Address):
        """
        Called when we fail to connect to an endpoint
        Args:
            err: Twisted Failure instance
            address: the address we failed to connect to
        """
        if type(err.value) == error.TimeoutError:
            logger.debug(f"Failed connecting to {address} connection timed out")
        elif type(err.value) == error.ConnectError:
            ce = err.value
            logger.debug(f"Failed connecting to {address} {ce.args[0].value}")
        else:
            logger.debug(f"Failed connecting to {address} {err.value}")
        self.RemoveKnownAddress(address)
        self.RemoveFromQueue(address)
        # if we failed to connect to new addresses, we should always add them to the DEAD_ADDRS list
        self.AddDeadAddress(address)

        # for testing
        # return err.type

    @staticmethod
    def Reset():
        NodeLeader._LEAD = None

        NodeLeader.Peers = []

        NodeLeader.KNOWN_ADDRS = []
        NodeLeader.DEAD_ADDRS = []

        NodeLeader.NodeId = None

        NodeLeader._MissedBlocks = []

        NodeLeader.BREQPART = 100
        NodeLeader.BREQMAX = 10000

        NodeLeader.KnownHashes = []
        NodeLeader.MissionsGlobal = []
        NodeLeader.MemPool = {}
        NodeLeader.RelayCache = {}

        NodeLeader.NodeCount = 0

        NodeLeader.CurrentBlockheight = 0

        NodeLeader.ServiceEnabled = False

        NodeLeader.peer_check_loop = None
        NodeLeader.peer_check_loop_deferred = None

        NodeLeader.check_bcr_loop = None
        NodeLeader.check_bcr_loop_deferred = None

        NodeLeader.memcheck_loop = None
        NodeLeader.memcheck_loop_deferred = None

        NodeLeader.blockheight_loop = None
        NodeLeader.blockheight_loop_deferred = None

        NodeLeader.task_handles = {}
