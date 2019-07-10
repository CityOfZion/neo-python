"""
Example of running a NEO node and receiving notifications when events
of a specific smart contract happen.

Events include Runtime.Notify, Runtime.Log, Storage.*, Execution.Success
and several more. See the documentation here:

http://neo-python.readthedocs.io/en/latest/smartcontracts.html
"""
import asyncio
from contextlib import suppress
from signal import SIGINT

from logzero import logger

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Network.p2pservice import NetworkService
from neo.Settings import settings
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.contrib.smartcontract import SmartContract

# If you want the log messages to also be saved in a logfile, enable the
# next line. This configures a logfile with max 10 MB and 3 rotations:
# settings.set_logfile("/tmp/logfile.log", max_bytes=1e7, backup_count=3)

# Setup the smart contract instance
smart_contract = SmartContract("6537b4bd100e514119e3a7ab49d520d20ef2c2a4")


# Register an event handler for Runtime.Notify events of the smart contract.
@smart_contract.on_notify
def sc_notify(event):
    logger.info("SmartContract Runtime.Notify event: %s", event)

    # Make sure that the event payload list has at least one element.
    if not isinstance(event.event_payload, ContractParameter) or event.event_payload.Type != ContractParameterType.Array or not len(event.event_payload.Value):
        return

    # The event payload list has at least one element. As developer of the smart contract
    # you should know what data-type is in the bytes, and how to decode it. In this example,
    # it's just a string, so we decode it with utf-8:
    logger.info("- payload part 1: %s", event.event_payload.Value[0].Value.decode("utf-8"))


async def custom_background_code():
    """ Custom code run in a background thread. Prints the current block height."""
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        await asyncio.sleep(15)


async def setup_and_start(loop):
    # Use TestNet
    settings.setup_testnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    p2p = NetworkService()
    loop.create_task(p2p.start())
    bg_task = loop.create_task(custom_background_code())

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(False)

    # Run all the things (blocking call)
    logger.info("Everything setup and running. Waiting for events...")
    return bg_task


async def shutdown():
    # cleanup any remaining tasks
    for task in asyncio.Task.all_tasks():
        with suppress(asyncio.CancelledError):
            task.cancel()
            await task


def system_exit():
    raise SystemExit


def main():
    loop = asyncio.get_event_loop()

    # because a KeyboardInterrupt is so violent it can shutdown the DB in an unpredictable state.
    loop.add_signal_handler(SIGINT, system_exit)
    main_task = loop.create_task(setup_and_start(loop))

    try:
        loop.run_forever()
    except SystemExit:
        logger.info("Shutting down...")
        p2p = NetworkService()
        loop.run_until_complete(p2p.shutdown())
        loop.run_until_complete(shutdown())
        loop.stop()
    finally:
        loop.close()

    Blockchain.Default().Dispose()


if __name__ == "__main__":
    main()
