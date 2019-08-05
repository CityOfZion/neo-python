import asyncio
import socket
import traceback
import errno
from contextlib import suppress
from datetime import datetime
from functools import partial
from socket import AF_INET as IP4_FAMILY
from typing import Optional, List

from neo.Core.TX.Transaction import Transaction as OrigTransaction
from neo.Network.common import msgrouter, wait_for
from neo.Network.common.singleton import Singleton
from neo.Network import utils as networkutils
from neo.Network.mempool import MemPool
from neo.Network.node import NeoNode
from neo.Network.protocol import NeoProtocol
from neo.Network.relaycache import RelayCache
from neo.Network.requestinfo import RequestInfo
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger('network')


class NodeManager(Singleton):
    PEER_QUERY_INTERVAL = 15
    NODE_POOL_CHECK_INTERVAL = 10  # 2.5 * PEER_QUERY_INTERVAL  # this allows for enough time to get new addresses

    ONE_MINUTE = 60

    MAX_ERROR_COUNT = 5  # maximum number of times adding a block or header may fail before we disconnect it
    MAX_TIMEOUT_COUNT = 15  # maximum count the node responds slower than our threshold

    MAX_NODE_POOL_ERROR = 2
    MAX_NODE_POOL_ERROR_COUNT = 0

    # we override init instead of __init__ due to the Singleton (read class documentation)
    def init(self):
        self.loop = asyncio.get_event_loop()
        self.max_clients = settings.CONNECTED_PEER_MAX
        self.min_clients = settings.CONNECTED_PEER_MIN
        self.id = id(self)
        self.mempool = MemPool()

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

        # a list for gathering tasks such that we can manually determine the order of shutdown
        self.tasks = []
        self.shutting_down = False

        self.relay_cache = RelayCache()

        msgrouter.on_addr += self.on_addr_received

        self.running = False

    async def start(self):
        host = 'localhost'
        port = settings.NODE_PORT
        proto = partial(NeoProtocol, nodemanager=self)

        try:
            await self.loop.create_server(proto, host, port)
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print(f"Node address {host}:{port} already in use ")
                raise SystemExit
            else:
                raise e
        print(f"[{datetime.now()}] Running P2P network on {host} {port}")

        for seed in settings.SEED_LIST:
            host, port = seed.split(':')
            if not networkutils.is_ip_address(host):
                try:
                    # TODO: find a way to make socket.gethostbyname non-blocking as it can take very long to look up
                    #       using loop.run_in_executor was unsuccessful.
                    host = networkutils.hostname_to_ip(host)
                except socket.gaierror as e:
                    logger.debug(f"Skipping {host}, address could not be resolved: {e}")
                    continue

            self.known_addresses.append(f"{host}:{port}")

        self.tasks.append(asyncio.create_task(self.handle_connection_queue()))
        self.tasks.append(asyncio.create_task(self.query_peer_info()))
        self.tasks.append(asyncio.create_task(self.ensure_full_node_pool()))

        self.running = True

    async def handle_connection_queue(self) -> None:
        while not self.shutting_down:
            addr, quality_check = await self.connection_queue.get()
            task = asyncio.create_task(self._connect_to_node(addr, quality_check))
            self.tasks.append(task)
            task.add_done_callback(lambda fut: self.tasks.remove(fut))

    async def query_peer_info(self) -> None:
        while not self.shutting_down:
            logger.debug(f"Connected node count {len(self.nodes)}")
            for node in self.nodes:
                task = asyncio.create_task(node.get_address_list())
                self.tasks.append(task)
                task.add_done_callback(lambda fut: self.tasks.remove(fut))
            await asyncio.sleep(self.PEER_QUERY_INTERVAL)

    async def ensure_full_node_pool(self) -> None:
        while not self.shutting_down:
            self.check_open_spots_and_queue_nodes()
            await asyncio.sleep(self.NODE_POOL_CHECK_INTERVAL)

    def check_open_spots_and_queue_nodes(self) -> None:
        open_spots = self.max_clients - (len(self.nodes) + len(self.queued_addresses))

        if open_spots > 0:
            logger.debug(f"Found {open_spots} open pool spots, trying to add nodes...")
            for _ in range(open_spots):
                try:
                    addr = self.known_addresses.pop(0)
                    self.queue_for_connection(addr)
                except IndexError:
                    # oh no, we've exhausted our good addresses list
                    if len(self.nodes) < self.min_clients:
                        if self.MAX_NODE_POOL_ERROR_COUNT != self.MAX_NODE_POOL_ERROR:
                            # give our `query_peer_info` loop a chance to collect new addresses
                            self.MAX_NODE_POOL_ERROR_COUNT += 1
                            break
                        else:
                            # we have no other option then to retry any address we know
                            logger.debug("Recycling old addresses")
                            self.known_addresses = self.bad_addresses
                            self.bad_addresses = []
                            self.MAX_NODE_POOL_ERROR_COUNT = 0

    def add_connected_node(self, node: NeoNode) -> None:
        if node not in self.nodes and not self.shutting_down:
            self.nodes.append(node)

        if node.address in self.queued_addresses:
            self.queued_addresses.remove(node.address)

    def remove_connected_node(self, node: NeoNode) -> None:
        with suppress(ValueError):
            self.queued_addresses.remove(node.address)

        with suppress(ValueError):
            self.nodes.remove(node)

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

    async def replace_node(self, node) -> None:
        if node.address not in self.bad_addresses:
            self.bad_addresses.append(node.address)

        asyncio.create_task(node.disconnect())

        with suppress(IndexError):
            addr = self.known_addresses.pop(0)
            self.queue_for_connection(addr)

    async def add_node_error_count(self, nodeid: int) -> None:
        node = self.get_node_by_nodeid(nodeid)
        if node:
            node.nodeweight.error_response_count += 1

            if node.nodeweight.error_response_count > self.MAX_ERROR_COUNT:
                logger.debug(f"Disconnecting node {node.nodeid} Reason: max error count threshold exceeded")
                await self.replace_node(node)

    async def add_node_timeout_count(self, nodeid: int) -> None:
        node = self.get_node_by_nodeid(nodeid)
        if node:
            node.nodeweight.timeout_count += 1

            if node.nodeweight.timeout_count > self.MAX_TIMEOUT_COUNT:
                logger.debug(f"Disconnecting node {node.nodeid} Reason: max timeout count threshold exceeded")
                await self.replace_node(node)

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
        if addr in self.bad_addresses or addr in self.queued_addresses or addr in self.known_addresses:
            # we received a duplicate
            return

        if addr not in self.connected_addresses():
            self.known_addresses.append(addr)
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
            logger.debug("WARNING QUALITY CHECK ADDR IS NONE!")
        if not healthy:
            with suppress(ValueError):
                self.known_addresses.remove(addr)

            if addr not in self.bad_addresses:
                self.bad_addresses.append(addr)

    def queue_for_connection(self, addr, only_quality_check=False) -> None:
        if only_quality_check:
            # quality check connections will disconnect after a successful handshake
            # they should not count towards the total connected nodes list
            logger.debug(f"Adding {addr} to connection queue for quality checking")
            task = asyncio.create_task(self.connection_queue.put((addr, only_quality_check)))
            self.tasks.append(task)
            task.add_done_callback(lambda fut: self.tasks.remove(fut))
        else:
            # check if there is space for another node according to our max clients settings
            if len(self.nodes) + len(self.queued_addresses) < self.max_clients:
                # regular connections should count towards the total connected nodes list
                if addr not in self.queued_addresses and addr not in self.connected_addresses():
                    self.queued_addresses.append(addr)
                    logger.debug(f"Adding {addr} to connection queue")
                    task = asyncio.create_task(self.connection_queue.put((addr, only_quality_check)))
                    self.tasks.append(task)
                    task.add_done_callback(lambda fut: self.tasks.remove(fut))

    def relay(self, inventory) -> bool:
        if type(inventory) is OrigTransaction or issubclass(type(inventory), OrigTransaction):
            success = self.mempool.add_transaction(inventory)
            if not success:
                return False

            # TODO: should we keep the tx in the mempool if relaying failed? There is currently no mechanism that retries sending failed tx's
            return wait_for(self.relay_directly(inventory))

    async def relay_directly(self, inventory) -> bool:
        relayed = False

        self.relay_cache.add(inventory)

        for node in self.nodes:
            relayed |= await node.relay(inventory)

        return relayed

    def reset_for_test(self) -> None:
        self.max_clients = settings.CONNECTED_PEER_MAX
        self.min_clients = settings.CONNECTED_PEER_MIN
        self.id = id(self)
        self.mempool.reset()
        self.nodes = []  # type: List[NeoNode]
        self.queued_addresses = []
        self.bad_addresses = []
        self.known_addresses = []
        self.connection_queue = asyncio.Queue()
        self.relay_cache.reset()

    """
    Internal helpers
    """

    async def _connect_to_node(self, address: str, quality_check=False, timeout=3) -> None:
        host, port = address.split(':')

        try:
            proto = partial(NeoProtocol, nodemanager=self, quality_check=quality_check)
            connect_coro = self.loop.create_connection(proto, host, port, family=IP4_FAMILY)
            # print(f"trying to connect to: {host}:{port}")
            await asyncio.wait_for(connect_coro, timeout)
            return
        except asyncio.TimeoutError:
            # print(f"{host}:{port} timed out")
            pass
        except OSError as e:
            # print(f"{host}:{port} failed to connect for reason {e}")
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print("ohhh, some error we didn't expect happened. Please create a Github issue and share the following stacktrace so we can try to resolve it")
            print("----------------[start of trace]----------------")
            traceback.print_exc()
            print("----------------[end of trace]----------------")

        with suppress(ValueError):
            self.queued_addresses.remove(address)

        with suppress(ValueError):
            self.known_addresses.remove(address)

        self.bad_addresses.append(address)

    async def shutdown(self) -> None:
        print("Shutting down node manager...", end='')
        self.shutting_down = True

        # shutdown all running tasks for this class
        # to prevent requeueing when disconnecting nodes
        logger.debug("stopping tasks...")
        for t in self.tasks:
            t.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # finally disconnect all existing connections
        # we need to create a new list to loop over, because `disconnect` removes items from self.nodes
        to_disconnect = list(map(lambda n: n, self.nodes))
        disconnect_tasks = []
        logger.debug("disconnecting nodes...")
        for n in to_disconnect:
            disconnect_tasks.append(asyncio.create_task(n.disconnect()))
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        print("DONE")
