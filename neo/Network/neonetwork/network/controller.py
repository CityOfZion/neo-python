import asyncio
import struct
from asyncio.streams import StreamReader, StreamWriter
from typing import TYPE_CHECKING, Optional
from neo.Network.neonetwork.core.uint256 import UInt256

CMD_HEADER_HASH_BY_HEIGHT = 'headerhash'
CMD_CUR_BLOCK_HEIGHT = 'blockheight'
CMD_CUR_HEADER_HEIGHT = 'headerheight'
CMD_ADD_HEADER = 'addheaders'
CMD_ADD_BLOCK = 'addblock'

if TYPE_CHECKING:
    from neo.Network.neonetwork.network import SyncManager


class TCPController:
    def __init__(self, syncmgr: 'SyncManager'):
        self.loop = asyncio.get_event_loop()
        self.syncmgr = syncmgr  # type: SyncManager
        self.reader = None
        self.writer = None
        self.io_lock = asyncio.Lock()

    async def read_cmd(self) -> Optional[str]:
        async with self.io_lock:
            try:
                task = asyncio.create_task(self.reader.readexactly(12))
                cmd = await asyncio.wait_for(task, timeout=0.001)
                cmd = cmd.decode().rstrip(' ')
                return cmd
            except asyncio.TimeoutError:
                task.exception()
                return None
            except BrokenPipeError:
                task.exception()
                pass

    async def safe_read(self, count):
        try:
            task = asyncio.create_task(self.reader.readexactly(count))
            data = await asyncio.gather(task)
            return data
        except BrokenPipeError:
            task.exception()

    def write_cmd(self, cmd) -> None:
        self.writer.write(cmd.ljust(12).encode())

    async def get_header_hash_by_height(self, height: int) -> UInt256:
        async with self.io_lock:
            # print(f"asking for hash for height {height}")
            self.write_cmd(CMD_HEADER_HASH_BY_HEIGHT)
            self.writer.write(struct.pack("I", height))

            data = await self.reader.readexactly(32)
            hash = UInt256(data=data)
            # print(f"received hash {data}")
            return hash

    async def get_current_header_height(self) -> int:
        async with self.io_lock:
            self.write_cmd(CMD_CUR_HEADER_HEIGHT)

            height = await self.reader.readexactly(4)
            height = struct.unpack("I", height)[0]
            # print(f"returned header height {height}")
            return height

    async def get_current_block_height(self) -> int:
        async with self.io_lock:
            self.write_cmd(CMD_CUR_BLOCK_HEIGHT)

            height = await self.reader.readexactly(4)
            height = struct.unpack("I", height)[0]
            # print(f"returned block height {height}")
            return height

    async def add_headers(self, headers) -> bool:
        async with self.io_lock:
            self.write_cmd(CMD_ADD_HEADER)
            len_headers = len(headers)
            self.writer.write(struct.pack("I", len_headers))
            for header in headers:
                data = header.to_array()
                self.writer.write(struct.pack("I", len(data)))
                self.writer.write(data)
            success = await self.reader.readexactly(1)
            return bool(success)

    async def add_block(self, block) -> bool:
        async with self.io_lock:
            self.write_cmd(CMD_ADD_BLOCK)
            # TODO: need full block implementation, otherwise we get 0 transactions when we serialize and that results
            #       in a deserialization error on the other side for now use raw_block to write back
            # data = block.to_array()
            data = block  # is actually the bytearray fromt he raw_block_cache
            self.writer.write(struct.pack("I", len(data)))
            self.writer.write(data)

            success = await self.reader.readexactly(1)
            return bool(success)

    async def handle_p2p_control_interface(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer

        addr = writer.get_extra_info('peername')
        print(f"Control client connected from {addr}")
        self.syncmgr.ledger_configured = True

        while True:
            cmd = await self.read_cmd()
            if not cmd:
                await asyncio.sleep(0.2)
                continue
        #
        #         if cmd == "nodelist":
        #             length = len(self.syncmgr.nodemgr.nodes)
        #             self.writer.write(struct.pack("I", length))

    async def start(self) -> None:
        server = await asyncio.start_server(self.handle_p2p_control_interface, '127.0.0.1', 9999)
        print(f"Controller serving on {server.sockets[0].getsockname()}")
        async with server:
            await server.serve_forever()
