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

# Smart contract event object (see also https://docs.python.org/3/library/collections.html#collections.namedtuple)
SmartContractEvent = namedtuple("SmartContractEvent", ["event_type", "event_payload", "contract_hash", "block_number", "tx_hash"])

# Smart contract event types
SMART_CONTRACT_RUNTIME_NOTIFY = "SMART_CONTRACT_RUNTIME_NOTIFY"  # payload: object[]
SMART_CONTRACT_RUNTIME_LOG = "SMART_CONTRACT_RUNTIME_LOG"        # payload: bytes

SMART_CONTRACT_EXECUTION_INVOKE = "SMART_CONTRACT_EXECUTION_INVOKE"
SMART_CONTRACT_EXECUTION_SUCCESS = "SMART_CONTRACT_EXECUTION_SUCCESS"
SMART_CONTRACT_EXECUTION_FAIL = "SMART_CONTRACT_EXECUTION_FAIL"


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
