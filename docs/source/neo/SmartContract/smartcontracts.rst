================================
Interacting with Smart Contracts
================================

A common use case for implementing neo-python is to interact with smart contracts. Typical smart contract events
include ``Runtime.Notify``, ``Runtime.Log``, execution success or failure and ``Storage.GET/PUT/DELETE``.

Event Types
"""""""""""""""""""""

This is a list of smart contract event types which can currently be handled with neo-python:

::

    RUNTIME_NOTIFY = "SmartContract.Runtime.Notify"
    RUNTIME_LOG = "SmartContract.Runtime.Log"

    EXECUTION = "SmartContract.Execution.*"
    EXECUTION_INVOKE = "SmartContract.Execution.Invoke"
    EXECUTION_SUCCESS = "SmartContract.Execution.Success"
    EXECUTION_FAIL = "SmartContract.Execution.Fail"

    STORAGE = "SmartContract.Storage.*"
    STORAGE_GET = "SmartContract.Storage.Get"
    STORAGE_PUT = "SmartContract.Storage.Put"
    STORAGE_DELETE = "SmartContract.Storage.Delete"


When such events occur in received blocks, a ``SmartContractEvent`` instance is dispatched through ``neo.EventHub``.

SmartContractEvent
""""""""""""""""""

The event handlers always receive a single argument, an instance of ``neo.EventHub.SmartContractEvent``, which
includes all the information about the current event. The ``SmartContractEvent`` has the following properties:

===================== ========= ==========
Property              Data type Info
===================== ========= ==========
``event_type``        str       One of the event types in ``neo.EventHub.SmartContractEvent``
``contract_hash``     UInt160   Hash of the contract
``tx_hash``           UInt256   Hash of the transaction
``block_number``      int       Block number this event was received at
``event_payload``     object[]  A list of objects, depending on what data types the smart contract emitted (eg. with ``Runtime.Notify``).
``execution_success`` bool      Whether the method invocation was successful
``test_mode``         bool      Whether this event was dispatched by a local TestInvoke instead of being received from the blockchain
===================== ========= ==========


neo.contrib.smartcontract.SmartContract
"""""""""""""""""""""""""""""""""""""""""""

Developers can easily subscribe to these events by using ``neo.contrib.smartcontract.SmartContract``.
This is an example of listening for ``Runtime.Notify`` events of a smart contract with the hash ``6537b4bd100e514119e3a7ab49d520d20ef2c2a4``:

::

    from neo.contrib.smartcontract import SmartContract

    smart_contract = SmartContract("6537b4bd100e514119e3a7ab49d520d20ef2c2a4")

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


The following decorators are currently available:

================= ======
Decorator         Smart contract events
================= ======
``@on_any``       all events
``@on_notify``    ``Runtime.Notify``
``@on_log``       ``Runtime.Log``
``@on_storage``   Storage PUT, GET and DELETE
``@on_execution`` Method invocation, success and failure
================= ======


Here is another example, showing how to listen for all events and distinguishing between event-types in your code:

::

    from neo.contrib.smartcontract import SmartContract
    from neo.EventHub import SmartContractEvent

    smart_contract = SmartContract("6537b4bd100e514119e3a7ab49d520d20ef2c2a4")

    @smart_contract.on_all
    def handle_sc_event(event):
        print("SmartContract Runtime.Notify event:", event)

        # Check if it is a Runtime.Notify event
        if event.event_type == SmartContractEvent.RUNTIME_NOTIFY:
            # Exit if an empty payload list
            if not len(event.event_payload):
                return

            # Decode the first payload item and print it
            print("- payload part 1:", event.event_payload[0].decode("utf-8"))
