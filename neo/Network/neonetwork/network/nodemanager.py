import asyncio
import json
import socket
import random
from neo.Network.neonetwork.common.singleton import Singleton
from neo.Network.neonetwork.common import msgrouter, wait_for
from neo.Network.neonetwork.network.node import NeoNode
from neo.Network.neonetwork.network.protocol import NeoProtocol
from neo.Network.neonetwork.network import utils as networkutils
from neo.Core.TX.Transaction import Transaction as OrigTransaction
from neo.Core.Blockchain import Blockchain as BC
from neo.Core.Block import Block as OrigBlock
from socket import AF_INET as IP4_FAMILY
from datetime import datetime
from functools import partial
from typing import Optional, List
from neo.Network.neonetwork.network.requestinfo import RequestInfo
from contextlib import suppress
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger('network')


class NodeManager(Singleton):
    PEER_QUERY_INTERVAL = 15
    NODE_POOL_CHECK_INTERVAL = 2.5 * PEER_QUERY_INTERVAL  # this allows for enough time to get new addresses

    ONE_MINUTE = 60

    MAX_ERROR_COUNT = 5  # maximum number of times adding a block or header may fail before we disconnect it
    MAX_TIMEOUT_COUNT = 15  # maximum count the node responds slower than our threshold

    # we override init instead of __init__ due to the Singleton (read class documentation)
    def init(self):
        self.loop = asyncio.get_event_loop()
        self.max_clients = 10
        self.min_clients = 4
        self.id = id(self)
        self.mempool = dict()

        # a list of nodes that we're actively using to request data from
        self.nodes = []  # type: List[NeoNode]
        # a list of host:port addresses that have a task pending to to connect to, but are not fully processed
        self.queued_addresses = []
        # a list of addresses which we know are bad. Reasons include; failed to connect, went offline, poor performance
        self.bad_addresses = []
        # a list of addresses that we've tested to be alive but that we're currently not connected to because we've
        # reached our `max_clients` setting. We use these addresses to quickly replace a bad node
        self.known_addresses = []

        self.connection_queue = asyncio.Queue()

        msgrouter.on_addr += self.on_addr_received
        msgrouter.on_block_persisted += self.update_mempool_for_block_persist

    async def start(self):
        host = 'localhost'
        port = 8888  # settings.NODE_PORT
        proto = partial(NeoProtocol, nodemanager=self)
        task = asyncio.create_task(self.loop.create_server(proto, host, port))
        await asyncio.gather(task)
        print(f"[{datetime.now()}] Running P2P network on {host} {port}")

        for seed in settings.SEED_LIST:
            self.queue_for_connection(seed)

        asyncio.create_task(self.handle_connection_queue())
        asyncio.create_task(self.query_peer_info())
        asyncio.create_task(self.ensure_full_node_pool())

    async def jitter(self) -> None:
        await asyncio.sleep(random.randint(0, 5) / 10)

    async def handle_connection_queue(self) -> None:
        while True:
            addr, quality_check = await self.connection_queue.get()
            print(f"attempting to connect to {addr} [quality: {quality_check}]")
            asyncio.create_task(self._connect_to_node(addr, quality_check))

    async def query_peer_info(self) -> None:
        while True:
            print(f"**********************  Connected node count {len(self.nodes)}")
            for node in self.nodes:
                asyncio.create_task(node.get_address_list())
            await asyncio.sleep(self.PEER_QUERY_INTERVAL)

    async def ensure_full_node_pool(self) -> None:
        # do a one time wait to allow collecting some initial addresses
        await asyncio.sleep(self.PEER_QUERY_INTERVAL + 5)

        max_errors = 2
        error_count = 0
        while True:
            open_spots = self.max_clients - (len(self.nodes) + len(self.queued_addresses))

            if open_spots > 0:
                print(f"Found {open_spots} open pool spots, trying to add nodes...")
            for _ in range(open_spots):
                try:
                    addr = self.known_addresses.pop(0)
                    self.queue_for_connection(addr)
                except IndexError:
                    # oh no, we've exhausted our good addresses list
                    if len(self.nodes) < self.min_clients:
                        if error_count != max_errors:
                            # give our `query_peer_info` loop a chance to collect new addresses
                            print("FAILLLLL")
                            error_count += 1
                            break
                        else:
                            print("RESETTING ADDRESSES")
                            # we have no other option then to retry any address we know
                            # TODO: add seedlist addresses that we're not still connected to
                            self.known_addresses = self.bad_addresses

            await asyncio.sleep(self.NODE_POOL_CHECK_INTERVAL)

    def add_connected_node(self, node: NeoNode) -> None:
        if node not in self.nodes:
            print(f"Added {node.address}")
            self.nodes.append(node)

        if node.address in self.queued_addresses:
            self.queued_addresses.remove(node.address)

    def remove_connected_node(self, node: NeoNode) -> None:
        with suppress(ValueError):
            self.queued_addresses.remove(node.address)

        with suppress(ValueError):
            self.nodes.remove(node)
            print(f"Removed {node.address}")

    def get_next_node(self, height: int) -> Optional[NeoNode]:
        """

        Args:
            height: the block height for which we're requesting data. Used to filter nodes that have this data

        Returns:

        """
        if len(self.nodes) == 0:
            return None

        weights = list(map(lambda n: n.nodeweight, self.nodes))
        # highest weight is taken first
        weights.sort(reverse=True)

        for weight in weights:
            node = self.get_node_by_nodeid(weight.id)
            if node and height <= node.best_height:
                return node
        else:
            # we could not find a node with the height we're looking for
            return None

    def replace_node(self, node) -> None:
        node.disconnect()

        with suppress(IndexError):
            addr = self.known_addresses.pop(0)
            self.queue_for_connection(addr)

    def add_node_error_count(self, nodeid: int) -> None:
        node = self.get_node_by_nodeid(nodeid)
        if node:
            node.nodeweight.error_response_count += 1

            if node.nodeweight.error_response_count > self.MAX_ERROR_COUNT:
                print(f"Disconnecting node {node.nodeid} Reason: max error count threshold exceeded")
                self.replace_node(node)

    def add_node_timeout_count(self, nodeid: int) -> None:
        node = self.get_node_by_nodeid(nodeid)
        if node:
            node.nodeweight.timeout_count += 1

            if node.nodeweight.timeout_count > self.MAX_TIMEOUT_COUNT:
                print(f"Disconnecting node {node.nodeid} Reason: max timeout count threshold exceeded")
                self.replace_node(node)

    def get_node_with_min_failed_time(self, ri: RequestInfo) -> Optional[NeoNode]:
        # Find the node with the least failures for the item in RequestInfo

        least_failed_times = 999
        least_failed_node = None
        tried_nodes = []

        while True:
            node = self.get_next_node(ri.height)
            if not node:
                return None

            failed_times = ri.failed_nodes.get(node.nodeid, 0)
            if failed_times == 0:
                # return the node we haven't tried this request on before
                return node

            if node.nodeid in tried_nodes:
                # we've exhausted the node list and should just go with our best available option
                return least_failed_node

            tried_nodes.append(node.nodeid)
            if failed_times < least_failed_times:
                least_failed_times = failed_times
                least_failed_node = node

    def get_node_by_nodeid(self, nodeid: int) -> Optional[NeoNode]:
        for n in self.nodes:
            if n.nodeid == nodeid:
                return n
        else:
            return None

    def connected_addresses(self) -> List[str]:
        return list(map(lambda n: n.address, self.nodes))

    def on_addr_received(self, addr) -> None:
        if addr in self.bad_addresses or addr in self.queued_addresses:
            # we received a duplicate
            return

        if addr not in self.connected_addresses():
            # it's a new address, see if we can make it part of the current connection pool
            if len(self.nodes) + len(self.queued_addresses) < self.max_clients:
                self.queue_for_connection(addr)
            else:
                # current pool is full, but..
                # we can test out the new addresses ahead of time as we might receive dead
                # or poor performing addresses from neo-cli nodes
                self.queue_for_connection(addr, only_quality_check=True)

    def quality_check_result(self, addr, healthy) -> None:
        if addr is None:
            print("*****************")
            print("***************** WARNING QUALITY CHECK ADDR IS NONE!")
            print("*****************")
        print(f"quality check {healthy} {addr}")
        if healthy and not addr in self.known_addresses:
            self.known_addresses.append(addr)
        else:
            if addr not in self.bad_addresses:
                self.bad_addresses.append(addr)

    def queue_for_connection(self, addr, only_quality_check=False) -> None:
        if only_quality_check:
            # quality check connections will disconnect after a successful handshake
            # they should not count towards the total connected nodes list
            print(f"Adding {addr} to connection queue for quality checking")
            asyncio.create_task(self.connection_queue.put((addr, only_quality_check)))
        else:
            # regular connections should count towards the total connected nodes list
            if addr not in self.queued_addresses and addr not in self.connected_addresses():
                self.queued_addresses.append(addr)
                print(f"Adding {addr} to connection queue")
                asyncio.create_task(self.connection_queue.put((addr, only_quality_check)))

    """
    Internal helpers
    """

    async def _connect_to_node(self, address: str, quality_check=False, timeout=3) -> None:
        host, port = address.split(':')
        if not networkutils.is_ip_address(host):
            try:
                # TODO: find a way to make socket.gethostbyname non-blocking as it can take very long to look up
                #       using loop.run_in_executor was unsuccessful.
                host = networkutils.hostname_to_ip(host)
            except socket.gaierror as e:
                print(f"Skipping {host}, address could not be resolved: {e}")
                return

        proto = partial(NeoProtocol, nodemanager=self, quality_check=quality_check)
        connect_coro = self.loop.create_connection(proto, host, port, family=IP4_FAMILY)

        try:
            await asyncio.wait_for(connect_coro, timeout)
            return
        except asyncio.TimeoutError:
            print(f"{host}:{port} timed out")
            pass
        except OSError as e:
            print(f"{host}:{port} failed to connect for reason {e}")
            pass
        except Exception as e:
            print(e)

        addr = f"{host}:{port}"
        with suppress(ValueError):
            self.queued_addresses.remove(addr)
        self.bad_addresses.append(addr)

    def relay(self, inventory):
        if type(inventory) is OrigTransaction or issubclass(type(inventory), OrigTransaction):
            success = self.add_transaction(inventory)
            if not success:
                return False

            return wait_for(self.relay_directly(inventory))

    def add_transaction(self, tx) -> bool:
        if BC.Default() is None:
            return False

        if tx.Hash in self.mempool.keys():
            return False

        if BC.Default().ContainsTransaction(tx.Hash):
            return False

        if not tx.Verify(self.mempool.values()):
            logger.error("Verifying tx result... failed")
            return False

        self.mempool[tx.Hash] = tx

        return True

    async def relay_directly(self, inventory) -> bool:
        relayed = False

        for node in self.nodes:
            relayed |= await node.relay(inventory)

        return relayed

    def update_mempool_for_block_persist(self, orig_block: OrigBlock):
        for tx in orig_block.Transactions:
            with suppress(KeyError):
                self.mempool.pop(tx.Hash)

    def reset_for_test(self):
        self.max_clients = 10
        self.min_clients = 4
        self.id = id(self)
        self.mempool = dict()
        self.nodes = []  # type: List[NeoNode]
        self.queued_addresses = []
        self.bad_addresses = []
        self.known_addresses = []
        self.connection_queue = asyncio.Queue()
