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
import pdb
# pymitter manages the event bus: https://github.com/riga/pymitter#examples
from pymitter import EventEmitter

# EventHub singleton which can be imported and used from all parts of the code
events = EventEmitter(wildcard=True)

# SmartContractEvent has the following properties:
#
# - event_type (str)
# - contract_hash (UInt160)
# - tx_hash (UInt256)
# - block_number (int)
# - event_payload (object[])
# - execution_success (bool)
#
#  `event_payload` is always a list of object, depending on what data types you sent in the smart contract.
SmartContractEvent = namedtuple("SmartContractEvent", ["event_type",
                                                       "event_payload",
                                                       "contract_hash",
                                                       "block_number",
                                                       "tx_hash",
                                                       "execution_success"])

# Smart contract event types
SMART_CONTRACT_RUNTIME_NOTIFY = "SMART_CONTRACT_RUNTIME_NOTIFY"  # payload: object[]
SMART_CONTRACT_RUNTIME_LOG = "SMART_CONTRACT_RUNTIME_LOG"        # payload: bytes

SMART_CONTRACT_EXECUTION_INVOKE = "SMART_CONTRACT_EXECUTION_INVOKE"
SMART_CONTRACT_EXECUTION_SUCCESS = "SMART_CONTRACT_EXECUTION_SUCCESS"
SMART_CONTRACT_EXECUTION_FAIL = "SMART_CONTRACT_EXECUTION_FAIL"


# Helper for easier dispatching of events from somewhere in the project
def dispatch_smart_contract_event(event_type,
                                  event_payload,
                                  contract_hash,
                                  block_number,
                                  tx_hash,
                                  execution_success=False):

    sc_event = SmartContractEvent(event_type, event_payload, contract_hash, block_number, tx_hash, execution_success)
    events.emit(event_type, sc_event)


#
# These handlers are only for temporary development and testing
#
#@events.on("*")
#def on_any_event(*args):
#    print("")
#    print("=EVENT:", [str(arg) for arg in args])
#    print("")


@events.on(SMART_CONTRACT_RUNTIME_LOG)
def on_sc_log(*args):
    if len(args) > 0 and type(args[0]) is SmartContractEvent:
        sc_event = args[0]
        print("[Log] [%s] %s" % (sc_event.contract_hash,sc_event.event_payload))


@events.on(SMART_CONTRACT_EXECUTION_SUCCESS)
def on_execution_succes(*args):

    if len(args) > 0 and type(args[0]) is SmartContractEvent:
        sc_event = args[0]
        print("[Execution Success] [%s] %s" % (sc_event.contract_hash,sc_event.event_payload))


@events.on(SMART_CONTRACT_EXECUTION_FAIL)
def on_execution_fail(*args):
    if len(args) > 0 and type(args[0]) is SmartContractEvent:
        sc_event = args[0]
        print("[Execution Fail] [%s] %s" % (sc_event.contract_hash,sc_event.event_payload))


        #print("sc event %s %s %s" % (len(args),args, type(args)))
#    pdb.set_trace()
