"""
Example of running a NEO node and receiving notifications when events
of a specific smart contract happen. This example also integrates
a simple REST API.

Start this example like this:

    API_TOKEN="test" python examples/smart-contract-rest-api.py

Example API calls:

    $ curl localhost:8080
    $ curl -H "Authorization: Bearer test" localhost:8080/echo/hello123
    $ curl -X POST -H "Authorization: Bearer test" -d '{ "msg": "foo" }' localhost:8080/echo-post

Smart contract events include Runtime.Notify, Runtime.Log, Storage.*,
Execution.Success and several more. See the documentation here:

http://neo-python.readthedocs.io/en/latest/smartcontracts.html

The REST API is using the Python package 'klein', which makes it
possible to create HTTP routes and handlers with Twisted in a
similar style to Flask. Klein is an official Twisted repository:
https://github.com/twisted/klein
"""
import os
import threading
import json
from time import sleep

from logzero import logger
from twisted.internet import reactor, task, endpoints
from twisted.web.server import Request, Site
from klein import Klein, resource

from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings

from neo.contrib.smartcontract import SmartContract
from neo.contrib.api.decorators import json_response, authenticated, catch_exceptions

SMART_CONTRACT_HASH = "6537b4bd100e514119e3a7ab49d520d20ef2c2a4"
LOGFILE = None
API_PORT = os.getenv("API_PORT", 8080)

# If LOGFILE is set, file logging will be setup with max 10 MB per file and 3 rotations:
if LOGFILE:
    settings.set_logfile(LOGFILE, max_bytes=1e7, backup_count=3)

# Setup the smart contract instance
smart_contract = SmartContract(SMART_CONTRACT_HASH)

# Setup the klein instance
app = Klein()


#
# Smart contract event handler for Runtime.Notify events
#
@smart_contract.on_notify
def sc_notify(event):
    print("SmartContract Runtime.Notify event:", event)

    # Make sure that the event payload list has at least one element.
    if not len(event.event_payload):
        return

    # The event payload list has at least one element. As developer of the smart contract
    # you should know what data-type is in the bytes, and how to decode it. In this example,
    # it's just a string, so we decode it with utf-8:
    print("- payload part 1:", event.event_payload[0].decode("utf-8"))


#
# Custom code that runs in the background
#
def custom_background_code():
    """ Custom code run in a background thread. Prints the current block height.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)


#
# REST API Routes
#
@app.route('/')
def home(request):
    return "Hello world"


@app.route('/echo/<msg>')
@catch_exceptions
@authenticated
@json_response
def echo_msg(request, msg):
    return {
        "echo": msg
    }

@app.route('/echo-post', methods=['POST'])
@catch_exceptions
@authenticated
@json_response
def echo_post(request):
    body = json.loads(request.content.read().decode("utf-8"))
    return {
        "post-body": body
    }

#
# Main method which starts everything up
#
def main():
    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)
    NodeLeader.Instance().Start()

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(False)

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Hook up Klein API to Twisted reactor
    endpoint_description = "tcp:port=%s:interface=localhost" % API_PORT
    endpoint = endpoints.serverFromString(reactor, endpoint_description)
    endpoint.listen(Site(app.resource()))

    # Run all the things (blocking call)
    logger.info("Everything setup and running. Waiting for events...")
    reactor.run()
    logger.info("Shutting down.")


if __name__ == "__main__":
    main()
