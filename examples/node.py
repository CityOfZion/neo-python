"""
Minimal NEO node with custom code in a background task.

It will log events from all smart contracts on the blockchain
as they are seen in the received blocks.
"""
import asyncio

from logzero import logger

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Network.p2pservice import NetworkService
from neo.Settings import settings


# If you want the log messages to also be saved in a logfile, enable the
# next line. This configures a logfile with max 10 MB and 3 rotations:
# settings.set_logfile("/tmp/logfile.log", max_bytes=1e7, backup_count=3)


async def custom_background_code():
    """ Custom code run in the background."""
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        await asyncio.sleep(15)


def main():
    # Use TestNet
    settings.setup_testnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    loop = asyncio.get_event_loop()
    # Start a reoccurring task with custom code
    loop.create_task(custom_background_code())
    p2p = NetworkService()
    loop.create_task(p2p.start())

    # block from here on
    loop.run_forever()

    # have a look at the other examples for handling graceful shutdown.


if __name__ == "__main__":
    main()
