import asyncio
import logging

from neo.Network.common.singleton import Singleton
from neo.Network.ledger import Ledger
from neo.Network.message import Message
from neo.Network.nodemanager import NodeManager
from neo.Network.syncmanager import SyncManager
from neo.Settings import settings

from contextlib import suppress


class NetworkService(Singleton):
    def init(self):
        self.loop = asyncio.get_event_loop()
        self.syncmgr = None
        self.nodemgr = None

        self.nodemgr_task = None

    async def start(self):
        Message._magic = settings.MAGIC
        self.nodemgr = NodeManager()
        self.syncmgr = SyncManager(self.nodemgr)
        ledger = Ledger()
        self.syncmgr.ledger = ledger

        logging.getLogger("asyncio").setLevel(logging.DEBUG)
        self.loop.set_debug(False)
        self.nodemgr_task = self.loop.create_task(self.nodemgr.start())
        self.loop.create_task(self.syncmgr.start())

    async def shutdown(self):
        if self.nodemgr_task and self.nodemgr_task.done():
            # starting nodemanager can fail if a port is in use, we need to retrieve and mute this exception on shutdown
            with suppress(SystemExit):
                self.nodemgr_task.exception()

        with suppress(asyncio.CancelledError):
            if self.syncmgr:
                await self.syncmgr.shutdown()

        with suppress(asyncio.CancelledError):
            if self.nodemgr:
                await self.nodemgr.shutdown()
