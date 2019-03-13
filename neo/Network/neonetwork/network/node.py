from neo.Network.neonetwork.network.message import Message
from neo.Network.neonetwork.network.payloads.version import VersionPayload
from neo.Network.neonetwork.network.payloads.getblocks import GetBlocksPayload
from neo.Network.neonetwork.network.payloads.addr import AddrPayload
from neo.Network.neonetwork.network.payloads.networkaddress import NetworkAddressWithTime
from neo.Network.neonetwork.network.payloads.inventory import InventoryPayload, InventoryType
from neo.Network.neonetwork.network.payloads.block import Block
from neo.Network.neonetwork.network.payloads.headers import HeadersPayload
from neo.Network.neonetwork.core.uint256 import UInt256
from neo.Network.neonetwork.core.header import Header
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import asyncio
from contextlib import suppress
from neo.Network.neonetwork.common import msgrouter
from neo.Network.neonetwork.network.nodeweight import NodeWeight
from neo.logging import log_manager

logger = log_manager.getLogger('network')

if TYPE_CHECKING:
    from neo.Network.neonetwork.network.nodemanager import NodeManager
    from neo.Network.neonetwork.network.protocol import NeoProtocol


class NeoNode:
    def __init__(self, protocol: 'NeoProtocol', nodemanager: 'NodeManager', quality_check=False):
        self.protocol = protocol
        self.nodemanager = nodemanager
        self.quality_check = quality_check

        self.address = None
        self.nodeid = id(self)
        self.version = None
        self.tasks = []
        self.nodeweight = NodeWeight(self.nodeid)
        self.best_height = 0  # track the block height of node

        self._inv_hash_for_height = None  # temp variable to track which hash we used for determining the nodes best height

    # connection setup and control functions
    async def connection_made(self, transport) -> None:
        # print(f"{id(self)} {transport.get_extra_info('peername')}")
        # can do things here like; check for reserved ips only, if addr is already in the connected list etc
        addr_tuple = self.protocol._stream_writer.get_extra_info('peername')
        self.address = f"{addr_tuple[0]}:{addr_tuple[1]}"

        # storing the task in case the connection is lost before it finishes the task, this allows us to cancel the task
        task = asyncio.create_task(self.do_handshake())
        self.tasks.append(task)
        with suppress(asyncio.TimeoutError):
            # await asyncio.wait_for(self.do_handshake(), timeout=2)
            await asyncio.wait_for(task, timeout=2)
            self.tasks.remove(task)

    async def do_handshake(self) -> None:
        send_version = Message(command='version', payload=VersionPayload(port=10333, userAgent="NEOPYTHON-PLUS-0.0.1"))
        await self.send_message(send_version)

        m = await self.read_message(timeout=3)
        if not m or m.command != 'version':
            self.disconnect()
            return

        if not self.validate_version(m.payload):
            self.disconnect()
            return

        m_verack = Message(command='verack')
        await self.send_message(m_verack)

        m = await self.read_message(timeout=3)
        if not m or m.command != 'verack':
            self.disconnect()
            return

        if self.quality_check:
            self.nodemanager.quality_check_result(self.address, healthy=True)
        else:
            print(f"Connected to {self.version.user_agent} @ {self.address}: {self.version.start_height}")
            self.nodemanager.add_connected_node(self)
            self.tasks.append(asyncio.create_task(self.run()))

    def disconnect(self) -> None:
        self.protocol.disconnect()

    def connection_lost(self, exc) -> None:
        print(f"{datetime.now()} Connection lost {self.address} {exc}")
        for t in self.tasks:
            t.cancel()
        self.nodemanager.remove_connected_node(self)
        if self.quality_check:
            self.nodemanager.quality_check_result(self.address, healthy=False)

    def validate_version(self, data) -> bool:
        try:
            self.version = VersionPayload.deserialize_from_bytes(data)
        except ValueError:
            print("failed to deserialize")
            return False

        if self.version.nonce == self.nodeid:
            print("client is self")
            return False

        # update nodes height indicator
        self.best_height = self.version.start_height

        # print("verification OK")
        return True

    async def run(self) -> None:
        print("Waiting for a message")
        while True:
            # we want to always listen for an incoming message
            message = await self.read_message(timeout=90)
            if not message:
                continue

            if message.command == 'addr':
                addr_payload = AddrPayload.deserialize_from_bytes(message.payload)
                for a in addr_payload.addresses:
                    msgrouter.on_addr(f"{a.address}:{a.port}")
            elif message.command == 'getaddr':
                await self.send_address_list()
            elif message.command == 'inv':
                inv = InventoryPayload.deserialize_from_bytes(message.payload)
                if not inv:
                    return

                if inv.type == InventoryType.block:
                    # neo-cli broadcasts INV messages on a regular interval. We can use those to determine their latest block height
                    # Hopefully NEO 3.0 has a better way to sync the nodes known height
                    if len(inv.hashes) > 0:
                        self._inv_hash_for_height = inv.hashes[-1]
                        await self.get_data(inv.type, inv.hashes)
                elif inv.type == InventoryType.consensus:
                    pass
                elif inv.type == InventoryType.tx:
                    pass
            elif message.command == 'block':
                block = Block.deserialize_from_bytes(message.payload)
                if block:
                    if self._inv_hash_for_height == block.hash and block.index > self.best_height:
                        logger.debug(f"Updating node height from {self.best_height} to {block.index}")
                        self.best_height = block.index
                        self._inv_hash_for_height = None

                    await msgrouter.on_block(self.nodeid, block, message.payload)
            elif message.command == 'headers':
                header_payload = HeadersPayload.deserialize_from_bytes(message.payload)

                if header_payload and len(header_payload.headers) > 0:
                    await msgrouter.on_headers(self.nodeid, header_payload.headers)
            else:
                if message.command not in ['consensus', 'getheaders']:
                    print(f"Message with command: {message.command}")

    # raw network commands
    async def get_address_list(self) -> None:
        """ Send a request for receiving known addresses"""
        m = Message(command='getaddr')
        await self.send_message(m)

    async def send_address_list(self) -> None:
        """ Send our known addresses """
        # TODO: figure out why neo-cli node stops responding to network data requests after we send addresses below
        # known_addresses = []
        # for node in self.nodemanager.nodes:
        #     host, port = node.address.split(':')
        #     if host and port:
        #         known_addresses.append(NetworkAddressWithTime(address=host, port=port))
        # if len(known_addresses) > 0:
        #     m = Message(command='address', payload=AddrPayload(addresses=known_addresses))
        #     await self.send_message(m)
        pass

    async def get_headers(self, hash_start: UInt256, hash_stop: Optional[UInt256] = None) -> None:
        """ Send a request for headers from `hash_start` + 1 to `hash_stop`

            Not specifying a `hash_stop` results in requesting at most 2000 headers.
        """
        m = Message(command='getheaders', payload=GetBlocksPayload(hash_start, hash_stop))
        await self.send_message(m)

    async def send_headers(self, headers: List[Header]) -> None:
        """ Send a list of Header objects.

            This is usually done as a response to a 'getheaders' request.
        """
        if len(headers) > 2000:
            headers = headers[:2000]

        m = Message(command='headers', payload=HeadersPayload(headers))
        await self.send_message(m)

    async def get_blocks(self, hash_start: UInt256, hash_stop: Optional[UInt256] = None) -> None:
        """ Send a request for blocks from `hash_start` + 1 to `hash_stop`

            Not specifying a `hash_stop` results in requesting at most 500 blocks.
        """
        m = Message(command='getblocks', payload=GetBlocksPayload(hash_start, hash_stop))
        await self.send_message(m)

    async def get_data(self, type: InventoryType, hashes: List[UInt256]) -> None:
        """ Send a request for receiving the specified inventory data."""
        if len(hashes) < 1:
            return

        m = Message(command='getdata', payload=InventoryPayload(type, hashes))
        await self.send_message(m)

    async def relay(self, inventory) -> bool:
        """
        
        Args:
            inventory: should be of type Block, Transaction or ConsensusPayload (see: InventoryType) 

        Returns:

        """
        # TODO: this is based on the current/old neo-python Block, Transaction and ConsensusPlayload classes
        #  meaning attribute naming will change (no longer camelCase) once we move to python naming convention
        inv = InventoryPayload(type=inventory.InventoryType, hashes=[inventory.Hash])
        m = Message(command='inv', payload=inv)
        await self.send_message()

        return True

    def send_tx(self) -> None:
        pass

    def send_block(self) -> None:
        pass

    def send_inv(self) -> None:
        pass

    def send_consensus(self) -> None:
        pass

    # convenience data request wrappers
    def convenience_get_headers(self, hash_start, hash_stop) -> List[Header]:
        # should call self.get_headers, wait for the network response and finally return the result
        # perhaps we can make this include `getdata.header`
        pass

    def convenience_get_blocks(self):
        # should call self.get_blocks, wait for the network response and finally return the result
        # perhaps we can make this include `getdata.block`
        pass

    def convenience_get_addresslist(self) -> List[NetworkAddressWithTime]:
        # should call self.get_address_list, wait for the network response and finally return the result
        pass

    # utility functions
    async def send_message(self, message: Message) -> None:
        await self.protocol.send_message(message)

    async def read_message(self, timeout: int = 30) -> Message:
        return await self.protocol.read_message(timeout)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.address == other.address and self.nodeid == other.nodeid
        else:
            return False
