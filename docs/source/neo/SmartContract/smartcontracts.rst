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

    VERIFICATION = "SmartContract.Verification.*"
    VERIFICATION_SUCCESS = "SmartContract.Verification.Success"
    VERIFICATION_FAIL = "SmartContract.Verification.Fail"

    STORAGE = "SmartContract.Storage.*"
    STORAGE_GET = "SmartContract.Storage.Get"
    STORAGE_PUT = "SmartContract.Storage.Put"
    STORAGE_DELETE = "SmartContract.Storage.Delete"

    CONTRACT = "SmartContract.Contract.*"
    CONTRACT_CREATED = "SmartContract.Contract.Create"
    CONTRACT_MIGRATED = "SmartContract.Contract.Migrate"
    CONTRACT_DESTROY = "SmartContract.Contract.Destroy"



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





Smart Contracts within the Prompt
"""""""""""""""""""""""""""""""""""""""""""

One of the most enjoyable features of ``neo-python`` is the ability to quickly build, test, import, and invoke smart contracts on the NEO platform.

This section is a basic guide on how to work with Smart Contracts in the Prompt.


Build Your Contract
^^^^^^^^^^^^^^^^^^^
The first step to using SC ( Smart Contracts ) within the prompt is to build one.  This is a convienience method which uses the ``neo-boa`` compiler to compiler your SC and save it in the ``.avm`` format.

When building or importing a file or contract within the prompt, it is always best to use a relative path ( relative to the ``neo-python`` installation directory), though an absolute path will most likely work as well.


This is sample1.py:

.. code-block:: python3

  def Main():
    print("Hello World")
    return True


.. code-block:: sh

  neo> build docs/source/example/sample1.py
  Saved output to docs/source/example/sample1.avm

This command simply compiles the file and nothing else.  You could now use the compiled ``.avm`` file to import in a later stage, or use another tool such as NEO-Gui to import your contract.


Build and test your contract
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build and test is a much more useful command, since it allows you to not only compile the file, but also execute and inspect the results.  The only drawback is that the syntax is bit more complicated

View ContractParameterType list :ref:`ContractParameterTypes`

The general syntax goes like this: ``build path/to/file.py test {input_params} {return_type} {needs_storage} {needs_dynamic_invoke} param1 param2 etc..`` where ``{input_params}`` and ``{return_type}``

- ``{input_params}`` is a single or series of ``ContractParameterType``, eg ``0710`` for an SC accepting a string and a list
- ``{return_type}`` is a single ``ContractParameterType``, eg ``02`` for an SC returning an integer
- ``{needs_storage}`` is a boolean, either ``True`` or ``False`` used to indicate whether or not the SC uses the ``Storage.Get/Put/Delete`` interop API
- ``{needs_dynamic_invoke}`` is also a boolean, indicating whether or not the SC will be calling another contract whose address it will not know until runtime.  This will most always be ``False``
- ``params1 params2 etc...`` These are the parameters you are testing with.

So for building and testing our ``sample1.py``, the syntax would be ``build docs/source/example/sample1.py test '' 01 False False``, where ``''`` indicates that no parameters are accepted and ``01`` indicates that it returns a boolean.  Lets try it out in the propmt

.. code-block:: sh

  neo> build docs/source/example/sample1.py test '' 01 False false
  Saved output to docs/source/example/sample1.avm
  please open a wallet to test built contract
  neo>

Ok, so it looks like we will need to open a wallet to test our contract! Note that after you open your wallet, you can use the up arrow key to select the previous command you entered.

.. code-block:: sh

  neo> open wallet Wallets/awesome
  [password]> ***********
  Opened wallet at Wallets/awesome
  neo> build docs/source/example/sample1.py test '' 01 False false
  Saved output to docs/source/example/sample1.avm
  [I 180302 22:22:58 Invoke:482] Used 0.016 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample1.py with arguments []
  Test deploy invoke successful
  Used total of 11 operations
  Result [{'type': 'Boolean', 'value': True}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

And you have now built and tested your first SC.  If you would like to view the results of same contract as an integer, you can change the ``return_type`` and you will get output like this:

.. code-block:: sh

  neo> build docs/source/example/sample1.py test '' 02 False False
  Saved output to docs/source/example/sample1.avm
  [I 180302 22:25:09 Invoke:482] Used 0.016 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample1.py with arguments []
  Test deploy invoke successful
  Used total of 11 operations
  Result [{'type': 'Integer', 'value': 1}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

You may have noticed that even though there is a ``print`` command in the contract, you didn not see anything printed out.  Lets fix that by turning on smart contract events and running it again.

.. code-block:: sh

  neo>
  neo> config sc-events on
  Smart contract event logging is now enabled
  neo> build docs/source/example/sample1.py test '' 01 False False
  Saved output to docs/source/example/sample1.avm
  [I 180302 22:56:19 EventHub:71] [test_mode][SmartContract.Contract.Create] [09a129673c61917593cb4b57dce066688f539d15] ['{\n    "version": 0,\n    "code": {\n        "hash": "0x09a129673c61917593cb4b57dce066688f539d15",\n        "script": "54c56b0b48656c6c6f20576f726c64680f4e656f2e52756e74696d652e4c6f67516c7566",\n        "parameters": "",\n        "returntype": 1\n    },\n    "name": "test",\n    "code_version": "test",\n    "author": "test",\n    "email": "test",\n    "description": "test",\n    "properties": {\n        "storage": false,\n        "dynamic_invoke": false\n    }\n}']
  [I 180302 22:56:19 EventHub:71] [test_mode][SmartContract.Runtime.Log] [09a129673c61917593cb4b57dce066688f539d15] [b'Hello World']
  [I 180302 22:56:19 EventHub:71] [test_mode][SmartContract.Execution.Success] [09a129673c61917593cb4b57dce066688f539d15] [1]
  [I 180302 22:56:20 Invoke:482] Used 0.016 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample1.py with arguments []
  Test deploy invoke successful
  Used total of 11 operations
  Result [{'type': 'Boolean', 'value': True}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>


So what happened there?  We turned on SmartContractEvent logging in the prompt with ``config sc-events on``.  Then after running the same command as before, we get 3 extra lines of output.

- **SmartContract.Contract.Create** is the event that created your SmartContract event in the VM
- **SmartContract.Runtime.Log** is the event where ``Hello World`` is printed for you
- **SmartContract.Execution.Success** indicates that the execution of the SC finished in a successful state


Ok now lets try a little more complex contract, detailed here as `sample2.py`

.. code-block:: python3

  def Main(operation, a, b):

      if operation == 'add':
          return a + b

      elif operation == 'sub':
          return a - b

      elif operation == 'mul':
          return a * b

      elif operation == 'div':
          return a / b

      else:
          return -1

We will build and run with a few paramaters:

.. code-block:: sh

  neo> build docs/source/example/sample2.py test 070202 02 False False
  Saved output to docs/source/example/sample2.avm
  [E 180302 22:30:01 ExecutionEngine:825] COULD NOT EXECUTE OP: Invalid list operation b'z' ROLL
  [E 180302 22:30:01 ExecutionEngine:826] Invalid list operation
  Traceback (most recent call last):
    File "/Users/thomassaunders/Workshop/neo-python/neo/VM/ExecutionEngine.py", line 823, in StepInto
      self.ExecuteOp(op, self.CurrentContext)
    File "/Users/thomassaunders/Workshop/neo-python/neo/VM/ExecutionEngine.py", line 276, in ExecuteOp
      estack.PushT(estack.Remove(n))
    File "/Users/thomassaunders/Workshop/neo-python/neo/VM/RandomAccessStack.py", line 57, in Remove
      raise Exception("Invalid list operation")
  Exception: Invalid list operation
  [I 180302 22:30:01 InteropService:93] Trying to get big integer Array: ['None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None']


Oh no, what happened there!  Oh, it looks like we tried to test a contract that wanted some parameters but didn't supply them.  Note than if you're building and testing contracts and you see an error similar to this, that is probably the issue you are running into.  Lets try that again with some parameters.

.. code-block:: sh

  neo> build docs/source/example/sample2.py test 070202 02 False False add 1 2
  Saved output to docs/source/example/sample2.avm
  [I 180302 22:32:06 Invoke:482] Used 0.033 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample2.py with arguments ['add', '1', '2']
  Test deploy invoke successful
  Used total of 39 operations
  Result [{'type': 'Integer', 'value': 3}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>
  neo> build docs/source/example/sample2.py test 070202 02 False False mul -1 20000
  Saved output to docs/source/example/sample2.avm
  [I 180302 22:33:36 Invoke:482] Used 0.041 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample2.py with arguments ['mul', '-1', '20000']
  Test deploy invoke successful
  Used total of 53 operations
  Result [{'type': 'Integer', 'value': -20000}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>


Ok much better. Now lets do something a bit more useful.  We will do a simple address balance tracker.

.. code-block:: python3

  from boa.interop.Neo.Storage import Get,Put,Delete,GetContext

  def Main(operation, addr, value):


      if not is_valid_addr(addr):
          return False

      ctx = GetContext()

      if operation == 'add':
          balance = Get(ctx, addr)
          new_balance = balance + value
          Put(ctx, addr, new_balance)
          return new_balance

      elif operation == 'remove':
          balance = Get(ctx, addr)
          Put(ctx, addr, balance - value)
          return balance - value

      elif operation == 'balance':
          return Get(ctx, addr)

      return False

  def is_valid_addr(addr):

      if len(addr) == 20:
          return True
      return False


We will do a test build with ``add`` and add some value to an address in my wallet.  You will notice that any address in your wallet will autocomplete as you type them, which is nice, but can be misleading.  When an address is sent into a SC through the ``prompt`` it is automatically converted to a ``ByteArray`` for your convienience.  So the method signature will look like ``070502`` or **String**, **ByteArray**, **Integer**

You will also notice that we are using ``True`` to indicate that we are using the ``Storage`` API of SC

.. code-block:: sh

  neo> build docs/source/example/sample3.py test 070502 02 True False add AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy 3
  Saved output to docs/source/example/sample3.avm
  [I 180302 23:04:33 Invoke:482] Used 1.174 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample3.py with arguments ['add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']
  Test deploy invoke successful
  Used total of 106 operations
  Result [{'type': 'Integer', 'value': 3}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

Invoke again and you will see that our test invokes persist the values in storage!

.. code-block:: sh

  neo> build docs/source/example/sample3.py test 070502 02 True False add AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy 3
  Saved output to docs/source/example/sample3.avm
  [I 180302 23:04:33 Invoke:482] Used 1.174 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample3.py with arguments ['add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']
  Test deploy invoke successful
  Used total of 106 operations
  Result [{'type': 'Integer', 'value': 6}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

Now remove some value

.. code-block:: sh

  neo> build docs/source/example/sample3.py test 070502 02 True False remove AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy 2
  Saved output to docs/source/example/sample3.avm
  [I 180302 23:09:21 Invoke:482] Used 1.176 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample3.py with arguments ['remove', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '2']
  Test deploy invoke successful
  Used total of 109 operations
  Result [{'type': 'Integer', 'value': 4}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

You can also pass in a ByteArray object for the address, and test that the ``is_valid_addr`` will return False before anything else happens, which will be interpreted as 0:

.. code-block:: sh

  neo> build docs/source/example/sample3.py test 070502 02 True False add bytearray(b'\x00\x01\x02\x03') 4
  Saved output to docs/source/example/sample3.avm
  [I 180302 23:12:43 Invoke:482] Used 0.041 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample3.py with arguments ['add', "bytearray(b'\\x00\\x01\\x02\\x03')", '4']
  Test deploy invoke successful
  Used total of 52 operations
  Result [{'type': 'Integer', 'value': 0}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>

Note that sending in the readable format of the address ( *AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy* ) is the same as sending in the script hash of the address.  We will try it out by getting the balance.  Note that I add an extra 0 at the end as the last parameter, since the SC is expecting a 3rd parameter:

.. code-block:: sh

  neo> build docs/source/example/sample3.py test 070502 02 True False balance bytearray(b'\x03\x19\xe0)\xb9%\x85w\x90\xe4\x17\x85\xbe\x9c\xce\xc6\xca\xb1\x98\x96') 0
  Saved output to docs/source/example/sample3.avm
  [I 180302 23:16:23 Invoke:482] Used 0.162 Gas

  -----------------------------------------------------------
  Calling docs/source/example/sample3.py with arguments ['balance', "bytearray(b'\\x03\\x19\\xe0)\\xb9%\\x85w\\x90\\xe4\\x17\\x85\\xbe\\x9c\\xce\\xc6\\xca\\xb1\\x98\\x96')", '0']
  Test deploy invoke successful
  Used total of 87 operations
  Result [{'type': 'Integer', 'value': 4}]
  Invoke TX gas cost: 0.0001
  -------------------------------------------------------------

  neo>


Hopefully this is enough to get you started with building and testing your Smart Contracts in the ``neo-python`` prompt.

Importing a Smart Contract
^^^^^^^^^^^^^^^^^^^^^^^^^^

Smart Contract importing is somewhat similar to the ``build .. test`` notation, though you do not need to send any parameters along with it.  The format is ``import contract path/to/sample2.avm {input_params} {return_type} {needs_storage} {needs_dynamic_invoke}``.  After running this command, if everything goes ok you will be prompted to add some metadata about the contract.  Once that is complete, you will then have the choice to actually deploy this Smart Contract on the network.  Beware that doing so will cost you some Gas!

.. code-block:: sh

  neo>
  neo> import contract docs/source/example/sample2.avm 070202 02 False False
  Please fill out the following contract details:
  [Contract Name] > Sample Calculator
  [Contract Version] > .01
  [Contract Author] > Thomas Saunders
  [Contract Email] > tom@cityofzion.io
  [Contract Description] > A test calculator contract
  Creating smart contract....
                 Name: A test calculator contract
              Version: .01
               Author: tom@cityofzion.io
                Email: tom@cityofzion.io
          Description: A test calculator contract
        Needs Storage: False
  Needs Dynamic Invoke: False
  {
    "hash": "0x86d58778c8d29e03182f38369f0d97782d303cc0",
    "script": "5ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c7566",
    "parameters": "070202",
    "returntype": "02"
  }
  Used 100.0 Gas

  -------------------------------------------------------------------------------------------------------------------------------------
  Test deploy invoke successful
  Total operations executed: 11
  Results:
  [<neo.Core.State.ContractState.ContractState object at 0x11435d2e8>]
  Deploy Invoke TX GAS cost: 90.0
  Deploy Invoke TX Fee: 0.0
  -------------------------------------------------------------------------------------------------------------------------------------

  Enter your password to continue and deploy this contract
  [password]>

Here is where, if you really really want to spend the Gas to deploy your contract, you can enter your password and the real magic begins:

.. code-block:: sh

  Enter your password to continue and deploy this contract
  [password]> ***********
  [I 180302 23:46:23 Transaction:611] Verifying transaction: b'f8ad261d28bf4bc5544e47f9bc3fff85f85ee674f14162dac81dd56bf73cf0a3'
  Relayed Tx: f8ad261d28bf4bc5544e47f9bc3fff85f85ee674f14162dac81dd56bf73cf0a3
  neo>

Now you have deployed your contract to the network. If all goes well, it will soon be deployed. To determine when it has been deployed, you can either search for the ``txid`` on the blockchain, or search for the contract hash

.. code-block:: sh

  neo> tx f8ad261d28bf4bc5544e47f9bc3fff85f85ee674f14162dac81dd56bf73cf0a3
  {
    "txid": "0xf8ad261d28bf4bc5544e47f9bc3fff85f85ee674f14162dac81dd56bf73cf0a3",
    "type": "InvocationTransaction",
    "version": 1,
    "attributes": [],
    [ MORE Output Omitted ]

  neo> contract 0x86d58778c8d29e03182f38369f0d97782d303cc0
  {
      "version": 0,
      "code": {
          "hash": "0x86d58778c8d29e03182f38369f0d97782d303cc0",
          "script": "5ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c7566",
          "parameters": "070202",
          "returntype": 2
      },
      "name": "A test calculator contract",
      "code_version": ".01",
      "author": "tom@cityofzion.io",
      "email": "tom@cityofzion.io",
      "description": "A test calculator contract",
      "properties": {
          "storage": false,
          "dynamic_invoke": false
      }
  }

  neo>

Now that you have deployed the contract on the network, you can interact with it with real InvocationTransactions!


Test Invoke Your Contracts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the contract is deployed, you can no longer interact and change and build it like you can with the ``build .. test`` command, but it is best to do ``testinvoke`` in order to determine how things work on the chain.

Now that we have deployed the *Calculator Contract* we can interact with it with the ``testinvoke`` command, as long as we know its script hash.  The syntax is ``testinvoke {contract_hash} param1 param2 .. etc``

.. code-block:: sh

  neo> testinvoke 0x86d58778c8d29e03182f38369f0d97782d303cc0 add 1 2
  Used 0.033 Gas

  -------------------------------------------------------------------------------------------------------------------------------------
  Test invoke successful
  Total operations: 39
  Results ['Integer: 3 ']
  Invoke TX GAS cost: 0.0
  Invoke TX fee: 0.0001
  -------------------------------------------------------------------------------------------------------------------------------------

  Enter your password to continue and invoke on the network

  [password]>


Once again, this invoke is only done locally.  It will not be run on the network until you input your password.   If you do not want to invoke on the network, you can simply input an incorrect password and it will cancel. Lets cancel the invoke, and then set ``config sc-events on`` to see exactly what is happening when you test invoke and then send it to the network:

.. code-block:: sh

  Enter your password to continue and invoke on the network

  [password]> **
  Incorrect password
  neo>
  neo> config sc-events on
  Smart contract event logging is now enabled
  neo>
  neo> testinvoke 0x86d58778c8d29e03182f38369f0d97782d303cc0 add 1 2
  [I 180303 07:38:58 EventHub:71] [test_mode][SmartContract.Execution.Success] [86d58778c8d29e03182f38369f0d97782d303cc0] [3]
  Used 0.033 Gas

  -------------------------------------------------------------------------------------------------------------------------------------
  Test invoke successful
  Total operations: 39
  Results ['Integer: 3 ']
  Invoke TX GAS cost: 0.0
  Invoke TX fee: 0.0001
  -------------------------------------------------------------------------------------------------------------------------------------

  Enter your password to continue and invoke on the network

  [password]> ***********
  [I 180303 07:39:04 Transaction:611] Verifying transaction: b'e0f4251a83f7081fb6fd94ce884d12b0bb597c1c1b3f1a89f07db68e114f4fa2'
  [I 180303 07:39:04 EventHub:89] [SmartContract.Verification.Success][433121] [4c896601a99d58e22c32dcadd24974ca24c10587] [tx e0f4251a83f7081fb6fd94ce884d12b0bb597c1c1b3f1a89f07db68e114f4fa2] [True]
  Relayed Tx: e0f4251a83f7081fb6fd94ce884d12b0bb597c1c1b3f1a89f07db68e114f4fa2
  neo>
  neo> [I 180303 07:39:31 EventHub:89] [SmartContract.Execution.Success][433122] [86d58778c8d29e03182f38369f0d97782d303cc0] [tx e0f4251a83f7081fb6fd94ce884d12b0bb597c1c1b3f1a89f07db68e114f4fa2] [3]
  neo>


You'll notice a few things here:

1. First is that when test invoking with ``sc-events on`` you'll see the *SmartContract.Execution.Success* event, and you'll also see that the event indicates the Execution was done in ``test_mode``.
2. Now you will see a *SmartContract.Verification.Success* event.  This tells you that the TX was signed correctly and will pass *Verification* as it is relayed to other nodes and ultimately in Consensus.
3. After sending the InvocationTransaction to the network, you'll get a TX id which you can use to look up the invocation.
4. Finally, after the TX has been processed by the network, the local VM runs your invocation, this time not in ``test_mode`` and you see the *SmartContract.Execution.Success* Event again.
