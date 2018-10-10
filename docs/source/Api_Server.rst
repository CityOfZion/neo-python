API Server
===========

The neo-python API server provides an API interface, which can be used to query the NEO Blockchain via JSON-RPC or REST.

Start JSON and REST API Server on Mainnet:

::

    $ np-api-server --mainnet --port-rpc 10332 --port-rest 80

Usage
-----

::

    $ np-api-server -h
    usage: np-api-server [-h]
                     (--mainnet | --testnet | --privnet | --coznet | --config CONFIG)
                     [--port-rpc PORT_RPC] [--port-rest PORT_REST]
                     [--logfile LOGFILE] [--syslog] [--syslog-local [0-7]]
                     [--disable-stderr] [--datadir DATADIR]
                     [--maxpeers MAXPEERS] [--wallet WALLET] [--host HOST]
                     [--extended-rpc]

    optional arguments:
      -h, --help            show this help message and exit
      --datadir DATADIR     Absolute path to use for database directories
      --maxpeers MAXPEERS   Max peers to use for P2P Joining
      --wallet WALLET       Open wallet. Will allow you to use methods that
                            require an open wallet
      --host HOST           Hostname ( for example 127.0.0.1)
      --extended-rpc        Use extended json-rpc api

    Network options:
      --mainnet             Use MainNet
      --testnet             Use TestNet
      --privnet             Use PrivNet
      --coznet              Use CozNet
      --config CONFIG       Use a specific config file

    Mode(s):
      --port-rpc PORT_RPC   port to use for the json-rpc api (eg. 10332)
      --port-rest PORT_REST
                            port to use for the rest api (eg. 80)

    Logging options:
      --logfile LOGFILE     Logfile
      --syslog              Log to syslog instead of to log file ('user' is the
                            default facility)
      --syslog-local [0-7]  Log to a local syslog facility instead of 'user'.
                            Value must be between 0 and 7 (e.g. 0 for 'local0').
      --disable-stderr      Disable stderr logger

Default JSON-RPC Command List
-----------------------------

.. list-table::
   :widths: 20 20 40 10
   :header-rows: 1
   
   * - Command
     - Reference
     - Explanations
     - Comments
   * - getaccountstate
     - <address>
     - Checks account asset information according to account address
     - 
   * - getassetstate 
     - <asset_id>
     - Queries asset information according to the specified asset number
     -
   * - getbalance
     - <asset_id>
     - Returns the balance of the corresponding asset in the wallet according to the specified asset number.
     - Need to open the wallet
   * - getbestblockhash
     -
     - Gets the hash of the tallest block in the main chain
     -
   * - getblock
     - | <hash or index>
       | [verbose=0]
       | [json=1]
     - Returns the corresponding block information according to the specified hash value or index
     -
   * - getblockcount
     -
     - Gets the number of blocks in the main chain
     -
   * - getblockhash
     - <index>
     - Returns the hash value of the corresponding block based on the specified index
     -
   * - getblocksysfee
     - <index>
     - Returns the system fees before the block according to the specified index
     -
   * - getconnectioncount
     - 
     - Gets the current number of connections for the node
     -
   * - getcontractstate
     - <script_hash>
     - Returns information about the contract based on the specified script hash
     -
   * - getnewaddress
     - 
     - Creates a new address
     - Need to open the wallet
   * - getrawmempool
     - 
     - Gets a list of unconfirmed transactions in memory
     -
   * - getrawtransaction
     - | <txid>
       | [verbose=0]
       | [json=1]
     - Returns the corresponding transaction information based on the specified hash value
     -
   * - getstorage
     - <script_hash> <key>
     - Returns the stored value based on the contract script hash and key
     -
   * - gettxout
     - <txid> <n>
     - Returns the corresponding transaction output (change) information based on the specified hash and index
     -
   * - getpeers
     -
     - Gets a list of nodes that are currently connected/disconnected by this node
     -
   * - getversion
     - 
     - Gets version information of this node
     -
   * - getwalletheight
     - 
     - Gets the current wallet index height.
     - Need to open the wallet
   * - invoke
     - <script_hash> <params>
     - Invokes a smart contract at specified script hash with the given parameters
     -
   * - invokefunction
     - <script_hash> <operation> <params>
     - Invokes a smart contract at specified script hash, passing in an operation and its params
     -
   * - invokescript
     - <script>
     - Runs a script through the virtual machine and returns the results
     -
   * - listaddress
     - 
     - Lists all the addresses in the current wallet.
     - Need to open the wallet
   * - sendrawtransaction
     - <hex>
     - Broadcast a transaction over the network.
     - 
   * - sendfrom
     - | <asset_id>
       | <address_from>
       | <address_to>
       | <value>
       | [fee=0]
       | [change_address]
     - Transfers from the specified address to the destination address.
     - Need to open the wallet
   * - sendtoaddress
     - | <asset_id>
       | <address_to>
       | <value>
       | [fee=0]
     - Transfer to specified address
     - Need to open the wallet
   * - sendmany
     - | <outputs_array>
       | [fee=0]
       | [change_address]
     - Bulk transfer order
     - Need to open the wallet
   * - validateaddress
     - <address>
     - Verify that the address is a correct NEO address	
     -    

Extended JSON-RPC Command List
------------------------------

.. list-table::
   :widths: 20 20 40 10
   :header-rows: 1
   
   * - Command
     - Reference
     - Explanations
     - Comments
   * - getnodestate
     - 
     - Returns real-time status of the node
     -
   * - gettxhistory
     - 
     - Returns a list of every tx in the associated wallet in JSON format, including block_index and blocktime
     - Need to open the wallet

POST Request Examples
---------------------

Bash Request Example
""""""""""""""""""""

Request using ``curl``:

::

    curl -X POST http://seed3.neo.org:10332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 2, "method": "getblockcount", "params": [] }'

After sending the request, you will get the following response:

::

    {"jsonrpc":"2.0","id":2,"result":2829911}

Script Request Example
""""""""""""""""""""""

::

    import requests
    import json


    url = "http://seed3.neo.org:10332"
    body = {"jsonrpc": "2.0", "id": 2, "method": "getblockcount", "params": []}
    res = requests.post(url, json=body)
    res = res.json()

    print("{}".format(json.dumps(res, indent=4)))

After running the script, you will receive the following response:

::

    {
        "jsonrpc": "2.0",
        "id": 2,
        "result": 2829945
    }

GET Request Example
-------------------

Script Request Example
""""""""""""""""""""""

::

    import requests
    import json

    res = requests.get('http://seed3.neo.org:10332?jsonrpc=2.0&id=2&method=getblockcount&params=[]')
    res = res.json()

    print("{}".format(json.dumps(res, indent=4)))

After running the script, you will receive the following response:

::

    {
        "jsonrpc": "2.0",
        "id": 2,
        "result": 2829945
    }
