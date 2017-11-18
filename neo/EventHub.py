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
from neo.UInt160 import UInt160
from neo.Cryptography.Crypto import Crypto
from neo.Settings import settings

# See https://logzero.readthedocs.io/en/latest/#example-usage
from logzero import logger

# pymitter manages the event dispatching (https://github.com/riga/pymitter#examples)
from pymitter import EventEmitter

# `events` is can be imported and used from all parts of the code to dispatch or receive events
events = EventEmitter(wildcard=True)


class SmartContractEvent:
    """
    SmartContractEvent is sent as argument to all smart contract event handlers. It
    includes all the information about the current event, such as type, payload,
    contract hash, transaction hash, and block number.

    - event_type (str)
    - contract_hash (UInt160)
    - tx_hash (UInt256)
    - block_number (int)
    - event_payload (object[])
    - execution_success (bool)
    - test_mode (bool)

    `event_payload` is always a list of object, depending on what data types you sent
    in the smart contract.
    """
    RUNTIME_NOTIFY = "SmartContract.Runtime.Notify"  # payload: object[]
    RUNTIME_LOG = "SmartContract.Runtime.Log"        # payload: bytes

    EXECUTION_INVOKE = "SmartContract.Execution.Invoke"
    EXECUTION_SUCCESS = "SmartContract.Execution.Success"
    EXECUTION_FAIL = "SmartContract.Execution.Fail"

    STORAGE = "SmartContract.Storage.*"
    STORAGE_GET = "SmartContract.Storage.Get"
    STORAGE_PUT = "SmartContract.Storage.Put"
    STORAGE_DELETE = "SmartContract.Storage.Delete"

    event_type = None
    event_payload = None
    contract_hash = None
    block_number = None
    tx_hash = None
    execution_success = None
    test_mode = None

    def __init__(self, event_type, event_payload, contract_hash, block_number, tx_hash, execution_success=False, test_mode=False):
        self.event_type = event_type
        self.event_payload = event_payload
        self.contract_hash = contract_hash
        self.block_number = block_number
        self.tx_hash = tx_hash
        self.execution_success = execution_success
        self.test_mode = test_mode

    def __str__(self):
        return "SmartContractEvent(event_type=%s, event_payload=%s, contract_hash=%s, block_number=%s, tx_hash=%s, execution_success=%s, test_mode=%s)" \
               % (self.event_type, self.event_payload, self.contract_hash, self.block_number, self.tx_hash, self.execution_success, self.test_mode)


# Helper for easier dispatching of events from somewhere in the project
def dispatch_smart_contract_event(event_type,
                                  event_payload,
                                  contract_hash,
                                  block_number,
                                  tx_hash,
                                  execution_success=False,
                                  test_mode=False):
    sc_event = SmartContractEvent(event_type, event_payload, contract_hash, block_number, tx_hash, execution_success, test_mode)
    events.emit(event_type, sc_event)


@events.on("SmartContract.*")
@events.on("SmartContract.*.*")
def on_sc_event(sc_event):
    if not settings.log_smart_contract_events:
        return

    if sc_event.test_mode:
        logger.info("[test_mode][%s] [%s] %s" % (sc_event.event_type, sc_event.contract_hash, sc_event.event_payload))
    else:
        logger.info("[%s][%s] [%s] [tx %s] %s" % (sc_event.event_type, sc_event.block_number, sc_event.contract_hash, sc_event.tx_hash.ToString(), sc_event.event_payload))


"""

#
# These handlers are only for temporary development and testing
#
@events.on(SmartContractEvent.EXECUTION_SUCCESS)
def on_execution_succes(sc_event):
    if sc_event.test_mode:
        print("[test_mode][Execution Success] [%s] %s" % (sc_event.contract_hash, sc_event.event_payload))
    else:
        print("[%s][Execution Success] [%s] [tx %s] %s" % (sc_event.block_number, sc_event.contract_hash, sc_event.tx_hash.ToString(), sc_event.event_payload))


@events.on(SmartContractEvent.RUNTIME_NOTIFY)
def on_sc_notify(sc_event):
    evt = sc_event.event_payload[0]
    if evt == b'transfer':
        pl = sc_event.event_payload[1:]
        addr_fr = Crypto.ToAddress(UInt160(data=pl[0]))
        addr_to = Crypto.ToAddress(UInt160(data=pl[1]))
        amount = int.from_bytes(pl[2], 'little') / 100000000
        print("[%s][Transfer] %s -> %s : %s " % (sc_event.block_number, addr_fr, addr_to, amount))
    else:
        if sc_event.test_mode:
            print("[test_mode][Notify][%s] %s" % (sc_event.contract_hash, sc_event.event_payload))
        else:
            print("[%s][Notify][%s] %s" % (
            sc_event.block_number, sc_event.contract_hash, sc_event.event_payload))


@events.on(SmartContractEvent.EXECUTION_FAIL)
def on_execution_fail(sc_event):
    if sc_event.test_mode:
        print("[test_mode][Execution Fail] [Error: %s] %s" % (sc_event.contract_hash, sc_event.event_payload))
    else:
        print("[%s][Execution Fail] [Error: %s] %s" % (sc_event.block_number, sc_event.contract_hash, sc_event.event_payload))


@events.on(SmartContractEvent.RUNTIME_LOG)
def on_sc_log(sc_event):
    if sc_event.test_mode:
        print("[test_mode][Log] [%s] %s" % (sc_event.contract_hash, sc_event.event_payload))
    else:
        print("[%s][Log] [%s] %s" % (sc_event.block_number, sc_event.contract_hash, sc_event.event_payload))




# This should allow you to listen to all storage events?

@events.on(SmartContractEvent.STORAGE)
def on_storage_event(sc_event):
    if sc_event.test_mode:
        print("[test_mode][%s] [%s] %s" % (sc_event.event_type, sc_event.contract_hash, sc_event.event_payload))
    else:
        print("[%s][%s] [%s] %s" % (sc_event.block_number, sc_event.event_type, sc_event.contract_hash, sc_event.event_payload))

@events.on_any
def on_any_event(*args):
    print("")
    print("=EVENT: %s" % args)
    print("")
"""
