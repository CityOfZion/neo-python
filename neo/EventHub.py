#
# This is the central event hub for blockchain and smart contract events,
# which makes it easy for external developers to receive notifications.
#
# Currently (pre-alpha) it works like this:
#
#   from neo.EventHub import events
#
#   @events.on("myevent")
#   def handler1(*args):
#       print("handler1 called with args", args)
#
from collections import namedtuple

# pymitter manages the event dispatching (https://github.com/riga/pymitter#examples)
from pymitter import EventEmitter

# `events` is a singleton which can be imported and used from all parts of the code
events = EventEmitter(wildcard=True)


class SmartContractEvent:
    """
    SmartContractEvent is sent as argument to all smart contract event handlers. It
    includes all the information about the current event, such as type, payload,
    contract hash, transaction hash, and block number.

    `event_payload` is always a list of object, depending on what data types you sent
    in the smart contract.
    """
    RUNTIME_NOTIFY = "SmartContract.RuntimeNotify"  # payload: object[]
    RUNTIME_LOG = "SmartContract.RuntimeLog"        # payload: bytes

    # EXECUTION_INVOKE = "SmartContract.ExecutionInvoke"
    # EXECUTION_SUCCESS = "SmartContract.ExecutionSuccess"
    # EXECUTION_FAIL = "SmartContract.ExecutionFail"

    event_type = None
    event_payload = None
    contract_hash = None
    block_number = None
    tx_hash = None

    def __init__(self, event_type, event_payload, contract_hash, block_number, tx_hash):
        self.event_type = event_type
        self.event_payload = event_payload
        self.contract_hash = contract_hash
        self.block_number = block_number
        self.tx_hash = tx_hash

    def __str__(self):
        return "SmartContractEvent(event_type=%s, event_payload=%s, contract_hash=%s, block_number=%s, tx_hash=%s)" % (self.event_type, self.event_payload, self.contract_hash, self.block_number, self.tx_hash)


# Helper for easier dispatching of events from somewhere in the project
def dispatch_smart_contract_event(event_type, event_payload, contract_hash, block_number, tx_hash):
    sc_event = SmartContractEvent(event_type, event_payload, contract_hash, block_number, tx_hash)
    events.emit(event_type, sc_event)


#
# These handlers are only for temporary development and testing
#
@events.on("*")
@events.on("*.*")
def on_any_event(*args):
    print("")
    print("=EVENT: %s" % args)
    print("")
