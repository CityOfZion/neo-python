import asyncio
import struct
from typing import Optional
from neo.Network.neonetwork.network.node import NeoNode
from neo.Network.neonetwork.network.message import Message
from asyncio.streams import StreamReader, StreamReaderProtocol, StreamWriter
from asyncio import events


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
        super().connection_lost(exc)
        if self.client:
            self.client.connection_lost(exc)

    def eof_received(self) -> bool:
        self._stream_reader.feed_eof()

        self.connection_lost()
        return True
        # False == Do not keep connection open, this makes sure that `connection_lost` gets called.
        # return False

    async def send_message(self, message: Message) -> None:
        self._stream_writer.write(message.to_array())
        try:
            await self._stream_writer.drain()
        except ConnectionResetError:
            print("connection reset")
            self.connection_lost(ConnectionResetError)
            self.disconnect()
        except ConnectionError:
            print("connection error")
            self.connection_lost(ConnectionError)
            self.disconnect()
        except asyncio.CancelledError:
            print("task cancelled, closing connection")
            self.connection_lost(asyncio.CancelledError)
            self.disconnect()
        except Exception as e:
            self.connection_lost()
            print(f"***** woah what happened here?! {str(e)}")
            self.disconnect()

    async def read_message(self, timeout: int = 30) -> Message:
        async def _read():
            try:
                message_header = await self._stream_reader.readexactly(24)
                magic, command, payload_length, checksum = struct.unpack('I 12s I I',
                                                                         message_header)  # uint32, 12byte-string, uint32, uint32

                payload_data = await self._stream_reader.readexactly(payload_length)
                payload, = struct.unpack('{}s'.format(payload_length), payload_data)

            except asyncio.IncompleteReadError:
                return None

            m = Message(magic, command.rstrip(b'\x00').decode('utf-8'), payload)

            if checksum != m.get_checksum(payload):
                print("Message checksum incorrect")
                return None
            else:
                return m

        try:
            return await asyncio.wait_for(_read(), timeout)
        except asyncio.TimeoutError:
            return None

    def disconnect(self) -> None:
        if self._stream_writer:
            self._stream_writer.close()
