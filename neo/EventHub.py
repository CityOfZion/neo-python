#
# This file is a simple EventEmitter singleton instance. You can use if from anywhere in the
# like this:
#
#   from neo.EventHub import events
#
#   @events.on("myevent")
#   def handler1(*args):
#       print("handler1 called with args", args)
#
# Dev Notes:
#
# EXECUTION_SUCCESS
#
#   Gets result value as type neo.VM.InteropService.ByteArray
#
from collections import namedtuple

# pymitter manages the event bus: https://github.com/riga/pymitter#examples
from pymitter import EventEmitter

# Instantiate event bus singleton, which can be imported and used from all parts of the code
events = EventEmitter(wildcard=True)

# Default smart contract event. See https://docs.python.org/3/library/collections.html#collections.namedtuple
SmartContractEvent = namedtuple("SmartContractEvent", ["contract_hash", "block_number", "transaction_id", "event_type", "event_payload"])

# Smart Contract Event Types
SMART_CONTRACT_RUNTIME_NOTIFY = "SMART_CONTRACT_RUNTIME_NOTIFY"  # payload: string
SMART_CONTRACT_RUNTIME_LOG = "SMART_CONTRACT_RUNTIME_LOG"        # payload: string

SMART_CONTRACT_EXECUTION_INVOKE = "SMART_CONTRACT_EXECUTION_INVOKE"
SMART_CONTRACT_EXECUTION_SUCCESS = "SMART_CONTRACT_EXECUTION_SUCCESS"
SMART_CONTRACT_EXECUTION_FAIL = "SMART_CONTRACT_EXECUTION_FAIL"

#
# These handlers are only for temporary development and testing
#
@events.on("*")
def on_any_event(*args):
    print("=EVENT:", args)
