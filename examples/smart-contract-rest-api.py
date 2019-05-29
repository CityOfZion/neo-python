"""
Example of running a NEO node, receiving smart contract notifications and
integrating a simple REST API.

Smart contract events include Runtime.Notify, Runtime.Log, Storage.*,
Execution.Success and several more. See the documentation here:
http://neo-python.readthedocs.io/en/latest/smartcontracts.html

This example optionally uses the environment variables NEO_REST_LOGFILE and NEO_REST_API_PORT.

Example usage (with "123" as valid API token):

    NEO_REST_API_TOKEN="123" python examples/smart-contract-rest-api.py

Example API calls:

    $ curl localhost:8080
    $ curl -H "Authorization: Bearer 123" localhost:8080/echo/hello123
    $ curl -X POST -H "Authorization: Bearer 123" -d '{ "hello": "world" }' localhost:8080/echo-post
"""
import asyncio
import os
from contextlib import suppress
from signal import SIGINT

from aiohttp import web
from logzero import logger

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Network.p2pservice import NetworkService
from neo.Settings import settings
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.contrib.smartcontract import SmartContract

# Set the hash of your contract here:
SMART_CONTRACT_HASH = "6537b4bd100e514119e3a7ab49d520d20ef2c2a4"

# Default REST API port is 8080, and can be overwritten with an env var:
API_PORT = os.getenv("NEO_REST_API_PORT", 8080)

# If you want to enable logging to a file, set the filename here:
LOGFILE = os.getenv("NEO_REST_LOGFILE", None)

# Internal: if LOGFILE is set, file logging will be setup with max
# 10 MB per file and 3 rotations:
if LOGFILE:
    settings.set_logfile(LOGFILE, max_bytes=1e7, backup_count=3)

# Internal: setup the smart contract instance
smart_contract = SmartContract(SMART_CONTRACT_HASH)


#
# Smart contract event handler for Runtime.Notify events
#


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


#
# Custom code that runs in the background
#
async def custom_background_code():
    """ Custom code run in a background thread. Prints the current block height.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        await asyncio.sleep(15)


#
# REST API Routes
#
async def home_route(request):
    return web.Response(body="hello world")


async def echo_msg(request):
    res = {
        "echo": request.match_info['msg']
    }
    return web.json_response(data=res)


async def echo_post(request):
    # Parse POST JSON body

    body = await request.json()

    # Echo it
    res = {
        "post-body": body
    }
    return web.json_response(data=res)


#
# Main setup method
#

async def setup_and_start(loop):
    # Use TestNet
    settings.setup_privnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    p2p = NetworkService()
    loop.create_task(p2p.start())
    bg_task = loop.create_task(custom_background_code())

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(False)

    app = web.Application()
    app.add_routes([
        web.route('*', '/', home_route),
        web.get("/echo-get/{msg}", echo_msg),
        web.post("/echo-post/", echo_post),
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", API_PORT)
    await site.start()

    # Run all the things (blocking call)
    logger.info("Everything setup and running. Waiting for events...")
    return site


async def shutdown():
    # cleanup any remaining tasks
    for task in asyncio.Task.all_tasks():
        with suppress((asyncio.CancelledError, Exception)):
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
        site = main_task.result()
        loop.run_until_complete(site.stop())

        p2p = NetworkService()
        loop.run_until_complete(p2p.shutdown())

        loop.run_until_complete(shutdown())
        loop.stop()
    finally:
        loop.close()

    logger.info("Closing databases...")
    Blockchain.Default().Dispose()


if __name__ == "__main__":
    main()
