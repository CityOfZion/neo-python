import asyncio
import struct
from typing import Optional
from neo.Network.node import NeoNode
from neo.Network.message import Message
from asyncio.streams import StreamReader, StreamReaderProtocol, StreamWriter
from asyncio import events
from neo.logging import log_manager

logger = log_manager.getLogger('network')


class NeoProtocol(StreamReaderProtocol):
    def __init__(self, *args, quality_check=False, **kwargs):
        """

        Args:
            *args:
            quality_check (bool): there are times when we only establish a connection to check the quality of the node/address
            **kwargs:
        """
        self._stream_reader = StreamReader()
        self._stream_writer = None
        nodemanager = kwargs.pop('nodemanager')
        self.client = NeoNode(self, nodemanager, quality_check)
        self._loop = events.get_event_loop()
        super().__init__(self._stream_reader)

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        super().connection_made(transport)
        self._stream_writer = StreamWriter(transport, self, self._stream_reader, self._loop)

        if self.client:
            asyncio.create_task(self.client.connection_made(transport))

    def connection_lost(self, exc: Optional[Exception] = None) -> None:
        if self.client:
            task = asyncio.create_task(self.client.connection_lost(exc))
            task.add_done_callback(lambda args: super(NeoProtocol, self).connection_lost(exc))
        else:
            super().connection_lost(exc)

    def eof_received(self) -> bool:
        self._stream_reader.feed_eof()

        self.connection_lost()
        return True
        # False == Do not keep connection open, this makes sure that `connection_lost` gets called.
        # return False

    async def send_message(self, message: Message) -> None:
        try:
            self._stream_writer.write(message.to_array())
            await self._stream_writer.drain()
        except ConnectionResetError:
            # print("connection reset")
            self.connection_lost(ConnectionResetError)
        except ConnectionError:
            # print("connection error")
            self.connection_lost(ConnectionError)
        except asyncio.CancelledError:
            # print("task cancelled, closing connection")
            self.connection_lost(asyncio.CancelledError)
        except Exception as e:
            # print(f"***** woah what happened here?! {traceback.format_exc()}")
            self.connection_lost()

    async def read_message(self, timeout: int = 30) -> Message:
        if timeout == 0:
            # avoid memleak. See: https://bugs.python.org/issue37042
            timeout = None

        async def _read():
            try:
                message_header = await self._stream_reader.readexactly(24)
                magic, command, payload_length, checksum = struct.unpack('I 12s I I',
                                                                         message_header)  # uint32, 12byte-string, uint32, uint32

                payload_data = await self._stream_reader.readexactly(payload_length)
                payload, = struct.unpack('{}s'.format(payload_length), payload_data)

            except Exception:
                # ensures we break out of the main run() loop of Node, which triggers a disconnect callback to clean up
                self.client.disconnecting = True
                return None

            m = Message(magic, command.rstrip(b'\x00').decode('utf-8'), payload)

            if checksum != m.get_checksum(payload):
                logger.debug("Message checksum incorrect")
                return None
            else:
                return m
        try:
            return await asyncio.wait_for(_read(), timeout)
        except Exception:
            return None

    def disconnect(self) -> None:
        if self._stream_writer:
            self._stream_writer.close()
