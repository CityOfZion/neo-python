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

# pymitter manages the event bus: https://github.com/riga/pymitter#examples
from pymitter import EventEmitter

# EventHub singleton which can be imported and used from all parts of the code
events = EventEmitter(wildcard=True)

# SmartContractEvent has the following properties:
#
# - event_type (str)
# - contract_hash (str)
# - tx_hash (str)
# - event_payload (object[])
#
#  `event_payload` is always a list of object, depending on what data types you sent in the smart contract.
SmartContractEvent = namedtuple("SmartContractEvent", ["event_type", "event_payload", "contract_hash", "block_number", "tx_hash"])

# Smart contract event types
SMART_CONTRACT_RUNTIME_NOTIFY = "SMART_CONTRACT_RUNTIME_NOTIFY"  # payload: object[]
SMART_CONTRACT_RUNTIME_LOG = "SMART_CONTRACT_RUNTIME_LOG"        # payload: bytes

SMART_CONTRACT_EXECUTION_INVOKE = "SMART_CONTRACT_EXECUTION_INVOKE"
SMART_CONTRACT_EXECUTION_SUCCESS = "SMART_CONTRACT_EXECUTION_SUCCESS"
SMART_CONTRACT_EXECUTION_FAIL = "SMART_CONTRACT_EXECUTION_FAIL"


# Helper for easier dispatching of events from somewhere in the project
def dispatch_smart_contract_event(event_type, event_payload, contract_hash, block_number, tx_hash):
    sc_event = SmartContractEvent(event_type, event_payload, contract_hash, block_number, tx_hash)
    events.emit(event_type, sc_event)


#
# These handlers are only for temporary development and testing
#
@events.on("*")
def on_any_event(*args):
    print("")
    print("=EVENT:", args)
    print("")
