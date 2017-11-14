import time

from collections import defaultdict
from functools import wraps

from neo.EventHub import events, SMART_CONTRACT_RUNTIME_NOTIFY, SMART_CONTRACT_RUNTIME_LOG


class SmartContract:
    """
    SmartContract is a helper for dApps to interact with smart contracts.
    In the current version it allows to get event callbackes, for instance
    on smart contract calls to `Runtime.Notify` or `Runtime.Log`:

        from neo.dapps.SmartContract import SmartContract

        smart_contract = SmartContract("6537b4bd100e514119e3a7ab49d520d20ef2c2a4")

        @smart_contract.on_notify
        def sc_notify(event):
            print("SmartContract Runtime.Notify event:", event)
            if len(event.event_payload):
                print(event.event_payload[0].decode("utf-8"))

    Handlers receive as `event` argument an instance of the
    `neo.EventHub.SmartContractEvent` object. It has the following properties:

    - event_type (str)
    - contract_hash (str)
    - tx_hash (str)
    - event_payload (object[])

    `event_payload` is always a list of object, depending on what data types you
    sent in the smart contract.
    """
    contract_hash = None
    event_handlers = defaultdict(list)

    def __init__(self, contract_hash):
        self.contract_hash = contract_hash
        assert contract_hash

        @events.on(SMART_CONTRACT_RUNTIME_NOTIFY)
        def call_on_notify(smart_contract_event):
            self._handle_event(SMART_CONTRACT_RUNTIME_NOTIFY, smart_contract_event)

    def _handle_event(self, event_type, smart_contract_event):
        if smart_contract_event.contract_hash != self.contract_hash:
            return

        # call event handlers. set(..) removes duplicates.
        handlers = set(self.event_handlers["*"] + self.event_handlers[event_type])
        [event_handler(smart_contract_event) for event_handler in handlers]

    def on_all(self, func):
        """ @on_all decorator: calls method on any event for this smart contract """
        return self._add_decorator("*", func)

    def on_notify(self, func):
        """ @on_notify decorator: calls method on Runtime.Notify events """
        return self._add_decorator(SMART_CONTRACT_RUNTIME_NOTIFY, func)

    def on_log(self, func):
        """ @on_log decorator: calls method on Runtime.Log events """
        # Append function to handler list
        return self._add_decorator(SMART_CONTRACT_RUNTIME_LOG, func)

    def _add_decorator(self, event_type, func):
        self.event_handlers[event_type].append(func)

        # Return the wrapper
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
