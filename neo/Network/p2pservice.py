import asyncio
import binascii
from asyncio.streams import StreamWriter, StreamReader
from socket import AF_INET as IPV4_FAMILY
import struct
from neo.IO.Helper import Helper as IOHelper
from neo.Settings import settings
from neo.Blockchain import GetBlockchain
from neo.Core.Header import Header
from neocore.UInt256 import UInt256

# TODO: get constants from neonetwork package
CMD_HEADER_HASH_BY_HEIGHT = 'headerhash'
CMD_CUR_BLOCK_HEIGHT = 'blockheight'
CMD_CUR_HEADER_HEIGHT = 'headerheight'

CMD_ADD_HEADERS = 'addheaders'
CMD_ADD_BLOCK = 'addblock'


class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass


class NetworkService(Singleton):
    def init(self):
        self.loop = asyncio.get_event_loop()
        self.reader = None
        self.writer = None
        self.ledger = GetBlockchain()
        self.io_lock = asyncio.Lock()

    async def read_cmd(self):
        try:
            cmd = await asyncio.wait_for(self.reader.readexactly(12), timeout=0.1)
        except asyncio.TimeoutError:
            return None

        cmd = cmd.decode().rstrip(' ')
        return cmd

    def write_cmd(self, cmd):
        self.writer.write(cmd.ljust(12).encode())

    async def get_nodes(self):
        async with self.io_lock:
            self.write_cmd("nodelist")
            node_count = await self.reader.readexactly(4)
            node_count = struct.unpack("I", node_count)
            return node_count

    async def start(self):
        print("starting network service")
        reader, writer = await asyncio.open_connection('127.0.0.1', 9999)  # type: StreamReader, StreamWriter
        self.reader = reader
        self.writer = writer

        while True:
            async with self.io_lock:
                cmd = await self.read_cmd()
                if not cmd:
                    await asyncio.sleep(0.2)
                    continue

                if cmd == CMD_HEADER_HASH_BY_HEIGHT:
                    height = await self.reader.readexactly(4)
                    height = struct.unpack("I", height)[0]

                    header_hash = self.ledger.GetHeaderHash(height)
                    if header_hash is None:
                        data = bytearray(32)
                    else:
                        data = bytearray(binascii.unhexlify(header_hash))
                        data.reverse()

                    self.writer.write(data)

                elif cmd == CMD_CUR_BLOCK_HEIGHT:
                    h = struct.pack("I", self.ledger.Height)
                    # print(f"block height {self.ledger.Height}")
                    self.writer.write(h)

                elif cmd == CMD_CUR_HEADER_HEIGHT:
                    hh = struct.pack("I", self.ledger.HeaderHeight)
                    # if hh > 0
                    # print(f"header height {self.ledger.HeaderHeight}")
                    self.writer.write(hh)
                elif cmd == CMD_ADD_HEADERS:
                    header_list_len = await self.reader.readexactly(4)
                    header_list_len = struct.unpack("I", header_list_len)[0]

                    headers = []
                    for _ in range(header_list_len):
                        header_len = await self.reader.readexactly(4)
                        header_len = struct.unpack("I", header_len)[0]
                        data = await self.reader.readexactly(header_len)

                        header = IOHelper.AsSerializableWithType(data, 'neo.Core.Header.Header')
                        if header is None:
                            self.writer.write(b'\x00')
                        else:
                            headers.append(header)

                    result = self.ledger.AddHeaders(headers)
                    if not result:
                        self.writer.write(b'\x00')
                    else:
                        self.writer.write(b'\x01')
                elif cmd == CMD_ADD_BLOCK:
                    block_len = await self.reader.readexactly(4)
                    block_len = struct.unpack("I", block_len)[0]
                    data = await self.reader.readexactly(block_len)

                    block = IOHelper.AsSerializableWithType(data, 'neo.Core.Block.Block')
                    if block is None:
                        self.writer.write(b'\x00')
                    else:
                        header_success = self.ledger.AddHeader(block.Header)
                        block_success = self.ledger.Persist(block)
                        if header_success and block_success:
                            self.writer.write(b'\x01')
                        else:
                            self.writer.write(b'\x00')
