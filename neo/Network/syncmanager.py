import asyncio
import traceback
from datetime import datetime
from neo.Network.core.header import Header
from typing import TYPE_CHECKING, List
from neo.Network.flightinfo import FlightInfo
from neo.Network.requestinfo import RequestInfo
from neo.Network.payloads.inventory import InventoryType
from neo.Network.common import msgrouter
from neo.Network.common.singleton import Singleton
from contextlib import suppress
from neo.Network.core.uint256 import UInt256

from neo.logging import log_manager

logger = log_manager.getLogger('syncmanager')
# log_manager.config_stdio([('syncmanager', 10)])

if TYPE_CHECKING:
    from neo.Network.nodemanager import NodeManager
    from neo.Network.payloads import Block


class SyncManager(Singleton):
    HEADER_MAX_LOOK_AHEAD = 6000
    HEADER_REQUEST_TIMEOUT = 5

    BLOCK_MAX_CACHE_SIZE = 500
    BLOCK_NETWORK_REQ_LIMIT = 500
    BLOCK_REQUEST_TIMEOUT = 5

    def init(self, nodemgr: 'NodeManager'):
        self.nodemgr = nodemgr
        self.controller = None
        self.block_requests = dict()  # header_hash:RequestInfo
        self.header_request = None  # type: RequestInfo
        self.ledger = None
        self.block_cache = []
        self.header_cache = []
        self.raw_block_cache = []
        self.is_persisting_blocks = False
        self.is_persisting_headers = False
        self.keep_running = True
        self.service_task = None
        self.persist_task = None
        self.health_task = None

        msgrouter.on_headers += self.on_headers_received
        msgrouter.on_block += self.on_block_received

    async def start(self) -> None:
        while not self.nodemgr.running:
            await asyncio.sleep(0.1)
        self.service_task = asyncio.create_task(self.run_service())
        self.health_task = asyncio.create_task(self.block_health())

    async def shutdown(self):
        print("Shutting down sync manager...", end='')
        self.keep_running = False
        self.block_cache = []
        shutdown_tasks = []

        # start up errors can cause the tasks to not have been assigned,
        # so we must validate their presence before feeding them to `gather`
        if self.service_task:
            shutdown_tasks.append(self.service_task)

        if self.health_task:
            shutdown_tasks.append(self.health_task)

        if self.persist_task:
            shutdown_tasks.append(self.persist_task)
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        print("DONE")

    async def block_health(self):
        # TODO: move this to nodemanager, once the network in general supports ping/pong
        #  we can then make smarter choices by looking at individual nodes advancing or not and dropping just those
        error_counter = 0
        last_height = await self.ledger.cur_block_height()
        while self.keep_running:
            await asyncio.sleep(15)
            cur_height = await self.ledger.cur_block_height()
            if cur_height == last_height:
                error_counter += 1
                if error_counter == 3:
                    to_disconnect = list(map(lambda n: n, self.nodemgr.nodes))
                    logger.debug(f"Block height not advancing. Replacing nodes: {to_disconnect}")
                    for n in to_disconnect:
                        await self.nodemgr.replace_node(n)
            else:
                error_counter = 0

            last_height = cur_height

    async def run_service(self):
        while self.keep_running:
            await self.check_timeout()
            await self.sync()
            await asyncio.sleep(1)

    async def sync(self) -> None:
        await self.sync_header()
        await self.sync_block()
        await self.persist_headers()
        if not self.is_persisting_blocks:
            self.persist_task = asyncio.create_task(self.persist_blocks())

    async def sync_header(self) -> None:
        if self.header_request:
            return

        cur_header_height = await self.ledger.cur_header_height()
        cur_block_height = await self.ledger.cur_block_height()
        if cur_header_height - cur_block_height >= self.HEADER_MAX_LOOK_AHEAD:
            return

        node = self.nodemgr.get_next_node(cur_header_height + 1)
        if not node:
            # No connected nodes or no nodes with our height. We'll wait for node manager to resolve this
            # or for the nodes to increase their height on the next produced block
            return

        self.header_request = RequestInfo(cur_header_height + 1)
        self.header_request.add_new_flight(FlightInfo(node.nodeid, cur_header_height + 1))

        cur_header_hash = await self.ledger.header_hash_by_height(cur_header_height)
        await node.get_headers(hash_start=cur_header_hash)

        logger.debug(f"Requested headers starting at {cur_header_height + 1} from node {node.nodeid_human}")
        node.nodeweight.append_new_request_time()

    async def persist_headers(self):
        self.is_persisting_headers = True
        if len(self.header_cache) > 0:
            while self.keep_running:
                try:
                    headers = self.header_cache.pop(0)
                    try:
                        await self.ledger.add_headers(headers)
                    except Exception as e:
                        print(traceback.format_exc())
                    await asyncio.sleep(0)
                except IndexError:
                    # cache empty
                    break

            # reset header_request such that the a new header sync task can be added
            self.header_request = None
            logger.debug("Finished processing headers")

        self.is_persisting_headers = False

    async def sync_block(self) -> None:
        # to simplify syncing, don't ask for more data if we still have requests in flight
        if len(self.block_requests) > 0:
            return

        # the block cache might not have been fully processed, so we want to avoid asking for data we actually already have
        best_block_height = await self.get_best_stored_block_height()
        cur_header_height = await self.ledger.cur_header_height()
        blocks_to_fetch = cur_header_height - best_block_height
        if blocks_to_fetch <= 0:
            return

        block_cache_space = self.BLOCK_MAX_CACHE_SIZE - len(self.block_cache)
        if block_cache_space <= 0:
            return

        if blocks_to_fetch > block_cache_space or blocks_to_fetch > self.BLOCK_NETWORK_REQ_LIMIT:
            blocks_to_fetch = min(block_cache_space, self.BLOCK_NETWORK_REQ_LIMIT)

        try:
            best_node_height = max(map(lambda node: node.best_height, self.nodemgr.nodes))
        except ValueError:
            # if the node list is empty max() fails on an empty list
            return

        node = self.nodemgr.get_next_node(best_node_height)
        if not node:
            # no nodes with our desired height. We'll wait for node manager to resolve this
            # or for the nodes to increase their height on the next produced block
            return

        hashes = []
        endheight = None
        for i in range(1, blocks_to_fetch + 1):
            next_block_height = best_block_height + i
            if self.is_in_blockcache(next_block_height):
                continue

            if next_block_height > best_node_height:
                break

            next_header_hash = await self.ledger.header_hash_by_height(next_block_height)
            if next_header_hash == UInt256.zero():
                # we do not have enough headers to fill the block cache. That's fine, just return
                break

            endheight = next_block_height
            hashes.append(next_header_hash)
            self.add_block_flight_info(node.nodeid, next_block_height, next_header_hash)

        if len(hashes) > 0:
            logger.debug(f"Asking for blocks {best_block_height + 1} - {endheight} from {node.nodeid_human}")
            await node.get_data(InventoryType.block, hashes)
            node.nodeweight.append_new_request_time()

    async def persist_blocks(self) -> None:
        self.is_persisting_blocks = True
        while self.keep_running:
            try:
                b = self.block_cache.pop(0)
                raw_b = self.raw_block_cache.pop(0)
                await self.ledger.add_block(raw_b)
                await asyncio.sleep(0.001)
            except IndexError:
                # cache empty
                break
        self.is_persisting_blocks = False

    async def check_timeout(self) -> None:
        task1 = asyncio.create_task(self.check_header_timeout())
        task2 = asyncio.create_task(self.check_block_timeout())
        try:
            await asyncio.gather(task1, task2)
        except Exception:
            logger.debug(traceback.format_exc())

    async def check_header_timeout(self) -> None:
        if not self.header_request:
            # no data requests outstanding
            return

        last_flight_info = self.header_request.most_recent_flight()

        now = datetime.utcnow().timestamp()
        delta = now - last_flight_info.start_time
        if delta < self.HEADER_REQUEST_TIMEOUT:
            # we're still good on time
            return

        node = self.nodemgr.get_node_by_nodeid(last_flight_info.node_id)
        if node:
            logger.debug(f"Header timeout limit exceeded by {delta - self.HEADER_REQUEST_TIMEOUT:.2f}s for node {node.nodeid_human}")

        cur_header_height = await self.ledger.cur_header_height()
        if last_flight_info.height <= cur_header_height:
            # it has already come in in the mean time
            # reset so sync_header will request new headers
            self.header_request = None
            return

        # punish node that is causing header_timeout and retry using another node
        self.header_request.mark_failed_node(last_flight_info.node_id)
        await self.nodemgr.add_node_timeout_count(last_flight_info.node_id)

        # retry with a new node
        node = self.nodemgr.get_node_with_min_failed_time(self.header_request)
        if node is None:
            # only happens if there are no nodes that have data matching our needed height
            self.header_request = None
            return

        hash = await self.ledger.header_hash_by_height(last_flight_info.height - 1)
        logger.debug(f"Retry requesting headers starting at {last_flight_info.height} from new node {node.nodeid_human}")
        await node.get_headers(hash_start=hash)

        # restart start_time of flight info or else we'll timeout too fast for the next node
        self.header_request.add_new_flight(FlightInfo(node.nodeid, last_flight_info.height))
        node.nodeweight.append_new_request_time()

    async def check_block_timeout(self) -> None:
        if len(self.block_requests) == 0:
            # no data requests outstanding
            return

        now = datetime.utcnow().timestamp()
        block_timeout_flights = dict()

        # test for timeout
        for block_hash, request_info in self.block_requests.items():  # type: _, RequestInfo
            flight_info = request_info.most_recent_flight()
            if now - flight_info.start_time > self.BLOCK_REQUEST_TIMEOUT:
                block_timeout_flights[block_hash] = flight_info

        if len(block_timeout_flights) == 0:
            # no timeouts
            return

        # 1) we first filter out invalid requests as some might have come in by now
        # 2) for each block_sync cycle we requested blocks in batches of max 500 per node, now when resending we try to
        #    create another batch
        # 3) Blocks arrive one by one in 'inv' messages. In the block_sync cycle we created a FlightInfo object per
        #    requested block such that we can determine speed among others. If one block in a request times out all
        #    others for the same request will of course do as well (as they arrive in a linear fashion from the same node).
        #    As such we only want to tag the individual node once (per request) for being slower than our timeout threshold not 500 times.
        remaining_requests = []
        nodes_to_tag_for_timeout = set()
        nodes_to_mark_failed = dict()

        best_stored_block_height = await self.get_best_stored_block_height()

        for block_hash, fi in block_timeout_flights.items():  # type: _, FlightInfo
            nodes_to_tag_for_timeout.add(fi.node_id)

            try:
                request_info = self.block_requests[block_hash]
            except KeyError:
                # means on_block_received popped it of the list
                # we don't have to retry for data anymore
                continue

            if fi.height <= best_stored_block_height:
                with suppress(KeyError):
                    self.block_requests.pop(block_hash)
                continue

            nodes_to_mark_failed[request_info] = fi.node_id
            remaining_requests.append((block_hash, fi.height, request_info))

        for nodeid in nodes_to_tag_for_timeout:
            await self.nodemgr.add_node_timeout_count(nodeid)

        for request_info, node_id in nodes_to_mark_failed.items():
            request_info.mark_failed_node(node_id)

        # for the remaining requests that need to be queued again, we create new FlightInfo objects that use a new node
        # and ask them in a single batch from that new node.
        hashes = []
        if len(remaining_requests) > 0:
            # retry the batch with a new node
            ri_first = remaining_requests[0][2]
            ri_last = remaining_requests[-1][2]

            # using `ri_last` because this has the highest block height and we want a node that supports that
            node = self.nodemgr.get_node_with_min_failed_time(ri_last)
            if not node:
                return

            for block_hash, height, ri in remaining_requests:  # type: _, int, RequestInfo
                ri.add_new_flight(FlightInfo(node.nodeid, height))

                hashes.append(block_hash)

            if len(hashes) > 0:
                logger.debug(f"Block time out for blocks {ri_first.height} - {ri_last.height}. Trying again using new node {node.nodeid_human} {hashes[0]}")
                await node.get_data(InventoryType.block, hashes)
                node.nodeweight.append_new_request_time()

    async def on_headers_received(self, from_nodeid, headers: List[Header]) -> int:
        if len(headers) == 0:
            return -1

        if self.header_request is None:
            return -2

        height = headers[0].index
        if height != self.header_request.height:
            # received headers we did not ask for
            return -3
        logger.debug(f"Headers received {headers[0].index} - {headers[-1].index}")

        if headers in self.header_cache:
            return -4

        cur_header_height = await self.ledger.cur_header_height()
        if height <= cur_header_height:
            return -5

        self.header_cache.append(headers)

        return 1

    async def on_block_received(self, from_nodeid, block: 'Block', raw_block) -> None:
        # TODO: take out raw_block and raw_block_cache once we can serialize a full block
        # print(f"{block.index} {block.hash} received")

        next_header_height = await self.ledger.cur_header_height() + 1
        if block.index > next_header_height:
            return

        cur_block_height = await self.ledger.cur_block_height()
        if block.index <= cur_block_height:
            return

        try:
            ri = self.block_requests.pop(block.hash)  # type: RequestInfo
            fi = ri.flights.pop(from_nodeid)  # type: FlightInfo
            now = datetime.utcnow().timestamp()
            delta_time = now - fi.start_time
            speed = (block._size / 1024) / delta_time  # KB/s

            node = self.nodemgr.get_node_by_nodeid(fi.node_id)
            if node:
                node.nodeweight.append_new_speed(speed)
        except KeyError:
            # it's a block we did not ask for
            # this can either be caused by rogue actors sending bad blocks
            # or as a reply to our `get_data` on a broadcasted `inv` message by the node.
            # (neo-cli nodes broadcast `inv` messages with their latest hash, we currently need to do a `get_data`
            # and receive the full block to know what their best height is as we have no other mechanism (yet))
            # TODO: remove once the network all start using neo-cli 2.10.1 or above which support ping/pong for height
            sync_distance = block.index - cur_block_height
            if sync_distance != 1:
                return
            # but if the distance is 1 we're in sync so we add the block anyway
            # to avoid having the `sync_block` task request the same data again
            # this is also necessary for neo-cli nodes because they maintain a TaskSession and refuse to send recently requested data

        if not self.is_in_blockcache(block.index) and self.keep_running:
            self.block_cache.append(block)
            self.raw_block_cache.append(raw_block)

    async def get_best_stored_block_height(self) -> int:
        """
        Helper to return the highest block in our possession (either in ledger or in block_cache)
        """
        best_block_cache_height = 0
        if len(self.block_cache) > 0:
            best_block_cache_height = self.block_cache[-1].index

        ledger_height = await self.ledger.cur_block_height()

        return max(ledger_height, best_block_cache_height)

    def is_in_blockcache(self, block_height: int) -> bool:
        for b in self.block_cache:
            if b.index == block_height:
                return True
        else:
            return False

    def add_block_flight_info(self, nodeid, height, header_hash) -> None:
        request_info = self.block_requests.get(header_hash, None)  # type: RequestInfo

        if request_info is None:
            # no outstanding requests for this particular hash, so we create it
            req = RequestInfo(height)
            req.add_new_flight(FlightInfo(nodeid, height))
            self.block_requests[header_hash] = req
        else:
            request_info.flights.update({nodeid: FlightInfo(nodeid, height)})

    def reset(self) -> None:
        self.header_request = None
        self.block_requests = dict()
        self.block_cache = []
        self.raw_block_cache = []
