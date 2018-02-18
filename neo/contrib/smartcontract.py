"""
Smart contract API to easily react to events from specific smart contracts.
"""
import time

from collections import defaultdict
from functools import wraps

from neo.EventHub import events, SmartContractEvent


class SmartContract:
    """
    SmartContract is a helper for dApps to interact with smart contracts.
    In the current version it allows to get event callbackes, for instance
    on smart contract calls to `Runtime.Notify` or `Runtime.Log`:

        from neo.contrib.smartcontract import SmartContract

        smart_contract = SmartContract("6537b4bd100e514119e3a7ab49d520d20ef2c2a4")

        @smart_contract.on_notify
        def sc_notify(event):
            print("SmartContract Runtime.Notify event:", event)
            if len(event.event_payload):
                print(event.event_payload[0].decode("utf-8"))

    Handlers receive as `event` argument an instance of the `neo.EventHub.SmartContractEvent`
    object. It has the following properties:

    - event_type (str)
    - contract_hash (UInt160)
    - tx_hash (UInt256)
    - block_number (int)
    - event_payload (object[])
    - execution_success (bool)
    - test_mode (bool)

    `event_payload` is always a list of objects, depending on what data types you
    sent in the smart contract.
    """
    contract_hash = None
    event_handlers = None

    def __init__(self, contract_hash):
        assert contract_hash
        self.contract_hash = str(contract_hash)
        self.event_handlers = defaultdict(list)

        # Handle EventHub events for SmartContract decorators
        @events.on(SmartContractEvent.RUNTIME_NOTIFY)
        @events.on(SmartContractEvent.RUNTIME_LOG)
        @events.on(SmartContractEvent.EXECUTION_SUCCESS)
        @events.on(SmartContractEvent.EXECUTION_FAIL)
        @events.on(SmartContractEvent.STORAGE)
        def call_on_event(sc_event):
            # Make sure this event is for this specific smart contract
            if str(sc_event.contract_hash) != self.contract_hash:
                return

            # call event handlers
            handlers = set(self.event_handlers["*"] + self.event_handlers[sc_event.event_type.rpartition('.')[0] + ".*"] + self.event_handlers[sc_event.event_type])  # set(..) removes duplicates
            [event_handler(sc_event) for event_handler in handlers]

    def on_any(self, func):
        """ @on_any decorator: calls method on any event for this smart contract """
        return self._add_decorator("*", func)

    def on_notify(self, func):
        """ @on_notify decorator: calls method on Runtime.Notify events """
        return self._add_decorator(SmartContractEvent.RUNTIME_NOTIFY, func)

    def on_log(self, func):
        """ @on_log decorator: calls method on Runtime.Log events """
        return self._add_decorator(SmartContractEvent.RUNTIME_LOG, func)

    def on_storage(self, func):
        """ @on_storage decorator: calls method on Neo.Storage.* events """
        return self._add_decorator(SmartContractEvent.STORAGE, func)

    def on_execution(self, func):
        """ @on_execution decorator: calls method on Neo.Execution.* events """
        return self._add_decorator(SmartContractEvent.EXECUTION, func)

    def _add_decorator(self, event_type, func):
        # First, add handler function to handlers
        self.event_handlers[event_type].append(func)

        # Return the wrapper
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
