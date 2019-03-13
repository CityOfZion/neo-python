import logging
import asyncio
from contextlib import suppress
from neo.Network.neonetwork.network.nodemanager import NodeManager
from neo.Network.neonetwork.network.syncmanager import SyncManager
from neo.Network.neonetwork.network.controller import TCPController
from neo.Network.neonetwork.ledger import Ledger

logger = logging.getLogger('NeoProtocol')


async def shutdown(loop):
    for task in asyncio.Task.all_tasks():
        task.cancel()


def main():
    nodemgr = NodeManager()
    syncmgr = SyncManager(nodemgr)
    controller = TCPController(syncmgr)
    ledger = Ledger(controller)
    syncmgr.ledger = ledger

    logging.getLogger("asyncio").setLevel(logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    task = loop.create_task(nodemgr.start())
    task.add_done_callback(lambda _: asyncio.create_task(syncmgr.start()))
    task.add_done_callback(lambda _: asyncio.create_task(controller.start()))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        with suppress(asyncio.CancelledError):
            loop.run_until_complete(asyncio.gather(shutdown(loop)))
            loop.stop()
    finally:
        loop.close()


if __name__ == "__main__":
    main()
