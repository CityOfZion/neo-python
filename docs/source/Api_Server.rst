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
   * - `getaccountstate`_
     - <address>
     - Checks account asset information according to account address
     - 
   * - `getassetstate`_ 
     - <assetId>
     - Queries asset information according to the specified asset number
     -
   * - `getbalance`_
     - <assetId>
     - Returns the balance of the corresponding asset in the wallet according to the specified asset number.
     - Need to open the wallet
   * - `getbestblockhash`_
     -
     - Gets the hash of the tallest block in the main chain
     -
   * - `getblock`_
     - | <index or hash>
       | [verbose=0]
     - Returns the corresponding block information according to the specified index or script hash
     -
   * - `getblockcount`_
     -
     - Gets the number of blocks in the main chain
     -
   * - `getblockhash`_
     - <index>
     - Returns the hash value of the corresponding block based on the specified index
     -
   * - `getblockheader`_
     - | <index or hash>
       | [verbose=0]
     - Returns the corresponding block header information according to the specified index or script hash
     -
   * - `getblocksysfee`_
     - <index>
     - Returns the system fees before the block according to the specified index
     -
   * - `getconnectioncount`_
     - 
     - Gets the current number of connections for the node
     -
   * - `getcontractstate`_
     - <script_hash>
     - Returns information about the contract based on the specified script hash
     -
   * - `getnewaddress`_
     - 
     - Creates a new address
     - Need to open the wallet
   * - `getrawmempool`_
     - 
     - Gets a list of unconfirmed transactions in memory
     -
   * - `getrawtransaction`_
     - | <txid>
       | [verbose=0]
     - Returns the corresponding transaction information based on the specified hash value
     -
   * - `getstorage`_
     - | <script_hash>
       | <key>
     - Returns the stored value based on the contract script hash and key
     -
   * - `gettxout`_
     - | <txid>
       | <n>
     - Returns the corresponding transaction output (change) information based on the specified hash and index
     -
   * - `getpeers`_
     -
     - Gets a list of nodes that are currently connected/disconnected by this node
     -
   * - `getversion`_
     - 
     - Gets version information of this node
     -
   * - `getwalletheight`_
     - 
     - Gets the current wallet index height.
     - Need to open the wallet
   * - `invoke`_
     - | <script_hash>
       | <params>
     - Invokes a smart contract at specified script hash with the given parameters
     -
   * - `invokefunction`_
     - | <script_hash>
       | <operation>
       | <params>
     - Invokes a smart contract at specified script hash, passing in an operation and its params
     -
   * - `invokescript`_
     - <script>
     - Runs a script through the virtual machine and returns the results
     -
   * - `listaddress`_
     - 
     - Lists all the addresses in the current wallet.
     - Need to open the wallet
   * - `sendrawtransaction`_
     - <hex>
     - Broadcast a transaction over the network.
     - 
   * - `sendfrom`_
     - | <assetId>
       | <address_from>
       | <address_to>
       | <value>
       | [fee=0]
       | [change_address]
     - Transfers from the specified address to the destination address, and you can specify a change address.
     - Need to open the wallet
   * - `sendtoaddress`_
     - | <assetId>
       | <address_to>
       | <value>
       | [fee=0]
     - Transfer to specified address
     - Need to open the wallet
   * - `sendmany`_
     - | <outputs_array>
       | [fee=0]
       | [change_address]
     - Bulk transfer order, and you can specify a change address.
     - Need to open the wallet
   * - `validateaddress`_
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
   * - `getnodestate`_
     - 
     - Returns the status of the node
     -
   * - `gettxhistory`_
     - 
     - Returns a list of every tx in the associated wallet in JSON format, including block_index and blocktime
     - Need to open the wallet

POST Request Examples
---------------------

Bash Request Example
""""""""""""""""""""

Request using ``curl``:

::

    curl -X POST http://seed3.neo.org:10332 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 1, "method": "getblockcount", "params": [] }'

After sending the request, you will get the following response:

::

    {"jsonrpc":"2.0","id":1,"result":2829911}

Script Request Example
""""""""""""""""""""""

::

    import requests
    import json


    url = "http://seed3.neo.org:10332"
    body = {"jsonrpc": "2.0", "id": 1, "method": "getblockcount", "params": []}
    res = requests.post(url, json=body)
    res = res.json()

    print("{}".format(json.dumps(res, indent=4)))

After running the script, you will receive the following response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 2829945
    }

GET Request Example
-------------------

Using A Script
""""""""""""""

::

    import requests
    import json

    res = requests.get('http://seed3.neo.org:10332?jsonrpc=2.0&id=1&method=getblockcount&params=[]')
    res = res.json()

    print("{}".format(json.dumps(res, indent=4)))

After running the script, you will receive the following response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 2829945
    }

Using Multi-Request in JSON-RPC
-------------------------------

neo-python supports multiple requests in one call by detecting list input.

Example
"""""""

Request Body:

::

    [
        {
            "jsonrpc": "2.0",
            "method": "getblock",
            "params": [1],
            "id": 1
        },
        {
            "jsonrpc": "2.0",
            "method": "getblock",
            "params": [1,1],
            "id": 2
        }
    ]

Response:

::

    [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": "00000000bf4421c88776c53b43ce1dc45463bfd2028e322fdfb60064be150ed3e36125d418f98ec3ed2c2d1c9427385e7b85d0d1a366e29c4e399693a59718380f8bbad6d6d90358010000004490d0bb7170726c59e75d652b5d3827bf04c165bbe9ef95cca4bf5501fd4501404edf5005771de04619235d5a4c7a9a11bb78e008541f1da7725f654c33380a3c87e2959a025da706d7255cb3a3fa07ebe9c6559d0d9e6213c68049168eb1056f4038a338f879930c8adc168983f60aae6f8542365d844f004976346b70fb0dd31aa1dbd4abd81e4a4aeef9941ecd4e2dd2c1a5b05e1cc74454d0403edaee6d7a4d4099d33c0b889bf6f3e6d87ab1b11140282e9a3265b0b9b918d6020b2c62d5a040c7e0c2c7c1dae3af9b19b178c71552ebd0b596e401c175067c70ea75717c8c00404e0ebd369e81093866fe29406dbf6b402c003774541799d08bf9bb0fc6070ec0f6bad908ab95f05fa64e682b485800b3c12102a8596e6c715ec76f4564d5eff34070e0521979fcd2cbbfa1456d97cc18d9b4a6ad87a97a2a0bcdedbf71b6c9676c645886056821b6f3fec8694894c66f41b762bc4e29e46ad15aee47f05d27d822f1552102486fd15702c4490a26703112a5cc1d0923fd697a33406bd5a1c00e0013b09a7021024c7b7fb6c310fccf1ba33b082519d82964ea93868d676662d4a59ad548df0e7d2102aaec38470f6aad0042c6e877cfd8087d2676b0f516fddd362801b9bd3936399e2103b209fd4f53a7170ea4444e0cb0a6bb6a53c2bd016926989cf85f9b0fba17a70c2103b8d9d5771d8f513aa0869b9cc8d50986403b78c6da36890638c3d46a5adce04a2102ca0e27697b9c248f6f16e085fd0061e26f44da85b58ee835c110caa5ec3ba5542102df48f60e8f3e01c48ff40b9b7f1310d7a8b2a193188befe1c2e3df740e89509357ae0100004490d0bb00000000"
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "hash": "0xd782db8a38b0eea0d7394e0f007c61c71798867578c77c387c08113903946cc9",
                "size": 686,
                "version": 0,
                "previousblockhash": "0xd42561e3d30e15be6400b6df2f328e02d2bf6354c41dce433bc57687c82144bf",
                "merkleroot": "0xd6ba8b0f381897a59396394e9ce266a3d1d0857b5e3827941c2d2cedc38ef918",
                "time": 1476647382,
                "index": 1,
                "nonce": "6c727071bbd09044",
                "nextconsensus": "APyEx5f4Zm4oCHwFWiSTaph1fPBxZacYVR",
                "script": {
                    "invocation": "404edf5005771de04619235d5a4c7a9a11bb78e008541f1da7725f654c33380a3c87e2959a025da706d7255cb3a3fa07ebe9c6559d0d9e6213c68049168eb1056f4038a338f879930c8adc168983f60aae6f8542365d844f004976346b70fb0dd31aa1dbd4abd81e4a4aeef9941ecd4e2dd2c1a5b05e1cc74454d0403edaee6d7a4d4099d33c0b889bf6f3e6d87ab1b11140282e9a3265b0b9b918d6020b2c62d5a040c7e0c2c7c1dae3af9b19b178c71552ebd0b596e401c175067c70ea75717c8c00404e0ebd369e81093866fe29406dbf6b402c003774541799d08bf9bb0fc6070ec0f6bad908ab95f05fa64e682b485800b3c12102a8596e6c715ec76f4564d5eff34070e0521979fcd2cbbfa1456d97cc18d9b4a6ad87a97a2a0bcdedbf71b6c9676c645886056821b6f3fec8694894c66f41b762bc4e29e46ad15aee47f05d27d822",
                    "verification": "552102486fd15702c4490a26703112a5cc1d0923fd697a33406bd5a1c00e0013b09a7021024c7b7fb6c310fccf1ba33b082519d82964ea93868d676662d4a59ad548df0e7d2102aaec38470f6aad0042c6e877cfd8087d2676b0f516fddd362801b9bd3936399e2103b209fd4f53a7170ea4444e0cb0a6bb6a53c2bd016926989cf85f9b0fba17a70c2103b8d9d5771d8f513aa0869b9cc8d50986403b78c6da36890638c3d46a5adce04a2102ca0e27697b9c248f6f16e085fd0061e26f44da85b58ee835c110caa5ec3ba5542102df48f60e8f3e01c48ff40b9b7f1310d7a8b2a193188befe1c2e3df740e89509357ae"
                },
                "tx": [
                    {
                        "txid": "0xd6ba8b0f381897a59396394e9ce266a3d1d0857b5e3827941c2d2cedc38ef918",
                        "size": 10,
                        "type": "MinerTransaction",
                        "version": 0,
                        "attributes": [],
                        "vout": [],
                        "vin": [],
                        "sys_fee": "0",
                        "net_fee": "0",
                        "scripts": [],
                        "nonce": 3151007812
                    }
                ],
                "confirmations": 2837625,
                "nextblockhash": "0xbf638e92c85016df9bc3b62b33f3879fa22d49d5f55d822b423149a3bca9e574"
            }
        }
    ]

Default RPC Method Details
--------------------------

getaccountstate
"""""""""""""""

Queries the account asset information, according to the account address.

Parameter Description
#####################

Account Address: A 34-bit length string, such as AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3.

Example
#######

Request body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getaccountstate", 
        "params": ["AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "version": 0,
            "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3",
            "script_hash": "c02e8d21ec52916a8182b1d7cde6ffef5cc0c91c",
            "frozen": false,
            "votes": [],
            "balances": {
                "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b": "50.0",
                "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7": "13.9998"
            }
        }
    }

Response Description:

* Address: Account Address, 34-bit length string
* Script_hash: Contract scipt hash; All accounts in NEO are contract accounts
* Frozen: Determine if the account is frozen
* Votes: Query the amount of NEO on that address used to vote
* Balances: Balances of assets at the address displayed using the assetId as the dict key followed by the asset amount as the value

return to the `Default JSON-RPC Command List`_

getassetstate
"""""""""""""

Queries the asset information, based on the specified asset number.

Parameter Description
#####################

assetId: asset identifier

* For NEO: c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b
* For GAS: 602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getassetstate", 
        "params": ["c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "assetId": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "assetType": 0,
            "name": "NEO",
            "amount": 10000000000000000,
            "available": 10000000000000000,
            "precision": 0,
            "fee": 0,
            "address": "0000000000000000000000000000000000000000",
            "owner": "00",
            "admin": "Abf2qMs1pzQb8kYk9RuxtUb9jtRKJVuBJt",
            "issuer": "Abf2qMs1pzQb8kYk9RuxtUb9jtRKJVuBJt",
            "expiration": 4000000,
            "is_frozen": false
        }
    }

return to the `Default JSON-RPC Command List`_

getbalance
""""""""""

Returns the balance of the corresponding asset in the wallet, based on the specified asset number. This method applies to global assets and the contract assets that conform to NEP-5 standards.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Parameter Description
#####################

assetId: asset identifier

* For NEO: "neo" or c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b
* For GAS: "gas" or 602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7

**-or-**

symbol or script hash of the contract for NEP5 tokens

A complete list of NEP5 tokens and hashes can be found `here <https://github.com/CityOfZion/neo-tokens/blob/master/tokenList.json>`_ or on your blockchain explorer of choice.

Examples
########

**Example 1: Inquiring the balance of global assets**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getbalance", 
        "params": ["neo"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "Balance": "150.0",
            "Confirmed": "50.0"
        }
    }

Response Description:

* balance: The actual balance of the asset in the wallet.
* confirmed: The exact amount of the asset in the wallet, where only confirmed amounts can be used for transfer.

``balance`` and ``confirmed`` values may not be equal. This happens when there is an output transaction from the wallet, and the change has not been confirmed yet, so the confirmed value will be less than the balance. Once the deal is confirmed, the two will become equal.

.. note:: Make sure your client has been fully synchronized to the latest block height before using this API, otherwise the balance returned may not be up-to-date.

**Example 2：Inquiring the balance of NEP-5 assets**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getbalance", 
        "params": ["NXT4"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "Balance": "2499000"
        }
    }

Response Description:

balance: the balance of the asset in the wallet. Since the NEP-5 assets adopt the balance system rather than the UTXO system, there is no confirmed in the returned result and the balance is the actual available balance.

.. note::   * Only when your client synchronizes to the block that the contract was deployed, execution of this API will return the correct value, otherwise execution of the API will result in an error.
            * When the input parameter is a script hash of a non-NEP-5 smart contract, execution of the API will result in an error.
            * Make sure your client has been fully synchronized to the latest block height before using this API, otherwise the balance returned may not be up-to-date.

return to the `Default JSON-RPC Command List`_

getbestblockhash
""""""""""""""""

Returns the hash of the tallest block in the main chain.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getbestblockhash", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "0xe10dbc9fed106953dd47bdd52d885c63b4171cdd9c430cf2b5a69bbd9ca0e02f"
    }

return to the `Default JSON-RPC Command List`_

getblock
""""""""

Returns the corresponding block information according to the specified index or hash value.

Parameter Description
#####################

Index: Block index (block height)

**-or-**

Hash: Block hash value

Verbose: Optional, the default value of verbose is 0. When verbose is 0, the serialized information of the block is returned, represented by a hexadecimal string. If you need to get detailed information, you will need to use the SDK for deserialization. When verbose is 1, detailed information of the corresponding block in Json format string, is returned.

Examples
########

**Example 1: Using a specified index, verbose=1**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblock", 
        "params": [1, 1]
    }


Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "hash": "0xd782db8a38b0eea0d7394e0f007c61c71798867578c77c387c08113903946cc9",
            "size": 686,
            "version": 0,
            "previousblockhash": "0xd42561e3d30e15be6400b6df2f328e02d2bf6354c41dce433bc57687c82144bf",
            "merkleroot": "0xd6ba8b0f381897a59396394e9ce266a3d1d0857b5e3827941c2d2cedc38ef918",
            "time": 1476647382,
            "index": 1,
            "nonce": "6c727071bbd09044",
            "nextconsensus": "APyEx5f4Zm4oCHwFWiSTaph1fPBxZacYVR",
            "script": {
                "invocation": "404edf5005771de04619235d5a4c7a9a11bb78e008541f1da7725f654c33380a3c87e2959a025da706d7255cb3a3fa07ebe9c6559d0d9e6213c68049168eb1056f4038a338f879930c8adc168983f60aae6f8542365d844f004976346b70fb0dd31aa1dbd4abd81e4a4aeef9941ecd4e2dd2c1a5b05e1cc74454d0403edaee6d7a4d4099d33c0b889bf6f3e6d87ab1b11140282e9a3265b0b9b918d6020b2c62d5a040c7e0c2c7c1dae3af9b19b178c71552ebd0b596e401c175067c70ea75717c8c00404e0ebd369e81093866fe29406dbf6b402c003774541799d08bf9bb0fc6070ec0f6bad908ab95f05fa64e682b485800b3c12102a8596e6c715ec76f4564d5eff34070e0521979fcd2cbbfa1456d97cc18d9b4a6ad87a97a2a0bcdedbf71b6c9676c645886056821b6f3fec8694894c66f41b762bc4e29e46ad15aee47f05d27d822",
                "verification": "552102486fd15702c4490a26703112a5cc1d0923fd697a33406bd5a1c00e0013b09a7021024c7b7fb6c310fccf1ba33b082519d82964ea93868d676662d4a59ad548df0e7d2102aaec38470f6aad0042c6e877cfd8087d2676b0f516fddd362801b9bd3936399e2103b209fd4f53a7170ea4444e0cb0a6bb6a53c2bd016926989cf85f9b0fba17a70c2103b8d9d5771d8f513aa0869b9cc8d50986403b78c6da36890638c3d46a5adce04a2102ca0e27697b9c248f6f16e085fd0061e26f44da85b58ee835c110caa5ec3ba5542102df48f60e8f3e01c48ff40b9b7f1310d7a8b2a193188befe1c2e3df740e89509357ae"
            },
            "tx": [
                {
                    "txid": "0xd6ba8b0f381897a59396394e9ce266a3d1d0857b5e3827941c2d2cedc38ef918",
                    "size": 10,
                    "type": "MinerTransaction",
                    "version": 0,
                    "attributes": [],
                    "vout": [],
                    "vin": [],
                    "sys_fee": "0",
                    "net_fee": "0",
                    "scripts": [],
                    "nonce": 3151007812
                }
            ],
            "confirmations": 2837710,
            "nextblockhash": "0xbf638e92c85016df9bc3b62b33f3879fa22d49d5f55d822b423149a3bca9e574"
        }
    }

**Example 2: Using a specified hash, verbose=0**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblock", 
        "params": ["0xd782db8a38b0eea0d7394e0f007c61c71798867578c77c387c08113903946cc9"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "00000000bf4421c88776c53b43ce1dc45463bfd2028e322fdfb60064be150ed3e36125d418f98ec3ed2c2d1c9427385e7b85d0d1a366e29c4e399693a59718380f8bbad6d6d90358010000004490d0bb7170726c59e75d652b5d3827bf04c165bbe9ef95cca4bf5501fd4501404edf5005771de04619235d5a4c7a9a11bb78e008541f1da7725f654c33380a3c87e2959a025da706d7255cb3a3fa07ebe9c6559d0d9e6213c68049168eb1056f4038a338f879930c8adc168983f60aae6f8542365d844f004976346b70fb0dd31aa1dbd4abd81e4a4aeef9941ecd4e2dd2c1a5b05e1cc74454d0403edaee6d7a4d4099d33c0b889bf6f3e6d87ab1b11140282e9a3265b0b9b918d6020b2c62d5a040c7e0c2c7c1dae3af9b19b178c71552ebd0b596e401c175067c70ea75717c8c00404e0ebd369e81093866fe29406dbf6b402c003774541799d08bf9bb0fc6070ec0f6bad908ab95f05fa64e682b485800b3c12102a8596e6c715ec76f4564d5eff34070e0521979fcd2cbbfa1456d97cc18d9b4a6ad87a97a2a0bcdedbf71b6c9676c645886056821b6f3fec8694894c66f41b762bc4e29e46ad15aee47f05d27d822f1552102486fd15702c4490a26703112a5cc1d0923fd697a33406bd5a1c00e0013b09a7021024c7b7fb6c310fccf1ba33b082519d82964ea93868d676662d4a59ad548df0e7d2102aaec38470f6aad0042c6e877cfd8087d2676b0f516fddd362801b9bd3936399e2103b209fd4f53a7170ea4444e0cb0a6bb6a53c2bd016926989cf85f9b0fba17a70c2103b8d9d5771d8f513aa0869b9cc8d50986403b78c6da36890638c3d46a5adce04a2102ca0e27697b9c248f6f16e085fd0061e26f44da85b58ee835c110caa5ec3ba5542102df48f60e8f3e01c48ff40b9b7f1310d7a8b2a193188befe1c2e3df740e89509357ae0100004490d0bb00000000"
    }

return to the `Default JSON-RPC Command List`_

getblockcount
"""""""""""""

Returns the number of blocks in the main chain.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockcount", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 2837737
    }

return to the `Default JSON-RPC Command List`_

getblockhash
""""""""""""

Returns the hash value of the corresponding block, based on the specified index.

Parameter Description
#####################

Index: Block index (block height)

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockhash", 
        "params": [1]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "0xd782db8a38b0eea0d7394e0f007c61c71798867578c77c387c08113903946cc9"
    }

return to the `Default JSON-RPC Command List`_

getblockheader
""""""""""""""

Returns the corresponding block header information according to the specified index or script hash.

Parameter Description
#####################

Index: Block index (block height)

**-or-**

Hash: Block hash value

Verbose: Optional, the default value of verbose is 0. When verbose is 0, the serialized information of the block is returned, represented by a hexadecimal string. If you need to get detailed information, you will need to use the SDK for deserialization. When verbose is 1, detailed information of the corresponding block in Json format string, is returned.

Examples
########

**Example 1: Using a specified index, verbose=1**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockheader", 
        "params": [1, 1]
    }


Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "hash": "0x98f293d6146f7e24bd6784a83cd961d68f57632b88a12452b5252e1690c4fb76",
            "size": 442,
            "version": 0,
            "previousblockhash": "0x996e37358dc369912041f966f8c5d8d3a8255ba5dcbd3447f8a82b55db869099",
            "merkleroot": "0xb04bea99a361209159d15fe99a12947a12e7466bc4c80ef24208c410d2217198",
            "time": 1539093502,
            "index": 1,
            "nonce": "c5bdd16b11ccd2f8",
            "nextconsensus": "AZ81H31DMWzbSnFDLFkzh9vHwaDLayV7fU",
            "script": {
                "invocation": "407b5e93aa64214274663cc8c8974d257e84ef439baeb09e5929240ee15e1cda950951d6dea86a05448df474f7fad74ea16b02af3a70e5dd566739313d8956b76d40fc4186ba58acc9e81c5e91db82dc30280bef14f4d6d378905b0dddd599b2e626c9b3d79aa2ec6c55874c47dd397440531bfbb846f9ad2d6e87c22a26531253b740eac04bd534713a6b2fdfeaecdb970dead0419a1fc490e16909dab2a357ec8d874c0211b21f1b33ce184c09987915080761aa3a9947efe5352db3adaf92a2aad4",
                "verification": "532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae"
            },
            "confirmations": 2026,
            "nextblockhash": "0x8dc77652c9f40e8999b710e886f861971f25014ff108086414a96ecac41cf180"
        }
    }

**Example 2: Using a specified hash, verbose=0**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblockheader", 
        "params": ["98f293d6146f7e24bd6784a83cd961d68f57632b88a12452b5252e1690c4fb76"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "00000000999086db552ba8f84734bddca55b25a8d3d8c5f866f941209169c38d35376e99987121d210c40842f20ec8c46b46e7127a94129ae95fd159912061a399ea4bb0feb3bc5b01000000f8d2cc116bd1bdc5be48d3a3f5d10013ab9ffee489706078714f1ea201c3407b5e93aa64214274663cc8c8974d257e84ef439baeb09e5929240ee15e1cda950951d6dea86a05448df474f7fad74ea16b02af3a70e5dd566739313d8956b76d40fc4186ba58acc9e81c5e91db82dc30280bef14f4d6d378905b0dddd599b2e626c9b3d79aa2ec6c55874c47dd397440531bfbb846f9ad2d6e87c22a26531253b740eac04bd534713a6b2fdfeaecdb970dead0419a1fc490e16909dab2a357ec8d874c0211b21f1b33ce184c09987915080761aa3a9947efe5352db3adaf92a2aad48b532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae00"
    }

return to the `Default JSON-RPC Command List`_

getblocksysfee
""""""""""""""

Returns the system fees of the block, based on the specified index.

Parameter Description
#####################

Index: Block index (block height)

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getblocksysfee", 
        "params": [1005434]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 19550000000000
    }

Response Description:

result：The system fees of the block, in GAS units.

return to the `Default JSON-RPC Command List`_

getconnectioncount
""""""""""""""""""

Returns the current number of connections for the node.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getconnectioncount", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 71
    }

return to the `Default JSON-RPC Command List`_

getcontractstate
""""""""""""""""

Queries contract information, according to the contract script hash.

Parameter Description
#####################

Script_hash：Contract script hash

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getcontractstate", 
        "params": ["3a4acd3647086e7c44398aac0349802e6a171129"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "version": 0,
            "code": {
                "hash": "0x3a4acd3647086e7c44398aac0349802e6a171129",
                "script": "0133c56b6a00527ac46a51527ac468164e656f2e53746f726167652e476574436f6e74657874616a52527ac4046e616d650673796d626f6c08646563696d616c730b746f74616c537570706c790962616c616e63654f66087472616e736665720c7472616e7366657246726f6d07617070726f766509616c6c6f77616e636559c176c96a53527ac468164e656f2e52756e74696d652e47657454726967676572616a54527ac46a54c30100876456006a52c3537c65af1c6a55527ac46a55c3640700516c7566616533236a56527ac46a56c31773656e745f66726f6d5f636f6e74726163745f61646472c3640700006c7566616a52c36a56c351527265a2166c7566616a54c3011087647302006a5b527ac46a53c3c06a5c527ac4616a5bc36a5cc39f647f006a53c36a5bc3c36a57527ac46a5bc351936a5b527ac46a00c36a57c38764d8ff682b53797374656d2e457865637574696f6e456e67696e652e47657443616c6c696e6753637269707448617368616a58527ac46a52c36a00c36a51c36a58c35379517955727551727552795279547275527275656e0f6c7566627cff6161616a00c30b63697263756c6174696f6e87640c006a52c365cd206c7566616a00c30d7465737457686974656c697374876428006a51c300c36a59527ac46a51c351c36a5a527ac46a52c36a59c36a5ac3527265791a6c7566616a00c30c70757457686974656c697374876410006a52c36a51c37c65f0186c7566616a00c30a6d696e74546f6b656e7387640c006a52c36588166c7566616a00c31263726f776473616c65417661696c61626c6587640c006a52c365d4206c7566616a00c3066465706c6f7987640900653c056c7566616a00c310696e697469616c697a654f776e6572738761640c006a52c365661d6c7566616a00c3096765744f776e65727387640c006a52c3659f1b6c7566616a00c30b636865636b4f776e65727387640e006a52c3537c65991a6c7566616a00c30b7377697463684f776e6572876410006a52c36a51c37c65fb196c7566616a00c3096f776e65724d696e74876410006a52c36a51c37c651f106c7566616a00c30f6d696772617465436f6e747261637487640c006a51c3658e026c7566616a00c30d6d696e7452656d61696e64657287640900653a006c75666107756e6b6e6f776e680f4e656f2e52756e74696d652e4c6f6711756e6b6e6f776e206f7065726174696f6e6c756661006c75660123c56b070080e03779c3116a00527ac40420f79b5b6a51527ac4070080e03779c3116a00527ac40420f79b5b6a51527ac4070080e03779c3116a00527ac40420f79b5b6a51527ac4070080e03779c3116a00527ac40420f79b5b6a51527ac4070080e03779c3116a00527ac40420f79b5b6a51527ac4070080e03779c3116a00527ac40420f79b5b6a51527ac468164e656f2e53746f726167652e476574436f6e74657874616a52527ac46a52c3537c653119630700006c7566616a52c365021b6346002d416c6c204f776e657273206d757374206d696e74206265666f7265206d696e74696e672072656d61696e646572680f4e656f2e52756e74696d652e4c6f67006c75666168134e656f2e52756e74696d652e47657454696d65616a53527ac46a53c36a51c39f640700006c7566616a00c36a52c365ce1d946a54527ac46a54c300a1642c00134e6f2072656d61696e696e6720746f6b656e73680f4e656f2e52756e74696d652e4c6f67006c756661682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e6753637269707448617368616a55527ac46a55c3653c1d6a56527ac46a52c36a56c37c680f4e656f2e53746f726167652e476574616a57527ac46a57c36a54c3936a58527ac46a52c36a56c36a58c35272680f4e656f2e53746f726167652e507574616a52c36a54c37c653d1d6a59527ac4006a55c36a54c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f746966796a59c36c75660119c56b6a00527ac468164e656f2e53746f726167652e476574436f6e74657874616a51527ac46a51c3537c657e17630700006c756661682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e67536372697074486173686165491c6a52527ac46a51c36a52c37c680f4e656f2e53746f726167652e476574616a53527ac46a53c300a0646b004c5143616e6e6f74206d696772617465207965742e2020506c65617365207472616e7366657220616c6c206e656f2f67617320616e6420746f6b656e732066726f6d20636f6e74726163742061646472657373680f4e656f2e52756e74696d652e4c6f67006c7566616a00c3c0599e642c001350726f76696465203920617267756d656e7473680f4e656f2e52756e74696d652e4c6f67006c7566616a00c300c36a54527ac46a00c351c36a55527ac46a00c352c36a56527ac46a00c353c36a57527ac46a00c354c36a58527ac46a00c355c36a59527ac46a00c356c36a5a527ac46a00c357c36a5b527ac46a00c358c36a5c527ac46a54c36a55c36a56c36a57c36a58c36a59c36a5ac36a5bc36a5cc3587951795a727551727557795279597275527275567953795872755372755579547957727554727568144e656f2e436f6e74726163742e4d696772617465616a5d527ac46a5dc36c75660114c56b0700c029f73d54056a00527ac40700c029f73d54056a00527ac40700c029f73d54056a00527ac40700c029f73d54056a00527ac40700c029f73d54056a00527ac40700c029f73d54056a00527ac468164e656f2e53746f726167652e476574436f6e74657874616a51527ac46a51c3537c654515630700006c7566616a51c30b696e697469616c697a65647c680f4e656f2e53746f726167652e4765746163c1006a51c30b696e697469616c697a6564515272680f4e656f2e53746f726167652e50757461682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e6753637269707448617368616a52527ac46a52c365bf196a53527ac46a51c36a53c36a00c35272680f4e656f2e53746f726167652e507574616a51c36a00c37c65ea196a54527ac4006a52c36a00c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f746966796a54c36c756661006c756656c56b6a00527ac46a51527ac46a52527ac46a00c36a51c36a52c37c6512197c680f4e656f2e53746f726167652e476574616c7566011fc56b6a00527ac46a51527ac46a52527ac46a53527ac46a54527ac46a51c3682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e67536372697074486173686187644b003243616e6e6f7420617070726f76652066726f6d20636f6e747261637420616464726573732e20557365207472616e73666572680f4e656f2e52756e74696d652e4c6f67006c7566616a54c3682953797374656d2e457865637574696f6e456e67696e652e476574456e74727953637269707448617368619e6499003e43616e6e6f742063616c6c2066726f6d20616e6f7468657220636f6e7472616374206f6e20626568616c66206f66206f7468657220616464726573736573680f4e656f2e52756e74696d652e4c6f672953657474696e672066726f6d206164647265737320746f2063616c6c696e6753637269707448617368680f4e656f2e52756e74696d652e4c6f676a54c36a51527ac4625200616a51c368184e656f2e52756e74696d652e436865636b5769746e6573736163300017496e73756666696369656e742070726976656c65676573680f4e656f2e52756e74696d652e4c6f67006c7566616a52c3c001149e640700006c7566616a53c3009f640700006c7566616a51c3654e176a55527ac46a00c36a55c37c680f4e656f2e53746f726167652e476574616a53c3a26485006a51c36a52c37c65f5166a56527ac46a53c300876422006a00c36a56c37c68124e656f2e53746f726167652e44656c65746561622100616a00c36a56c36a53c35272680f4e656f2e53746f726167652e50757461616a51c36a52c36a53c3527207617070726f766554c168124e656f2e52756e74696d652e4e6f74696679516c756661126e6f7420656e6f7567682062616c616e6365680f4e656f2e52756e74696d652e4c6f67006c75660120c56b6a00527ac46a51527ac46a52527ac46a53527ac46a53c300a1640700006c7566616a51c36a52c37c6525166a54527ac46a54c3c001319e640700006c7566616a00c36a54c37c680f4e656f2e53746f726167652e476574616a55527ac46a55c36a53c39f6438001b496e73756666696369656e742066756e647320617070726f76656468124e656f2e52756e74696d652e4e6f7469667961006c7566616a51c365d7156a56527ac46a52c365cc156a57527ac46a00c36a56c37c680f4e656f2e53746f726167652e476574616a58527ac46a58c36a53c39f64400023496e73756666696369656e7420746f6b656e7320696e2066726f6d2062616c616e636568124e656f2e52756e74696d652e4e6f7469667961006c7566616a00c36a57c37c680f4e656f2e53746f726167652e476574616a59527ac46a58c36a53c3946a5a527ac46a59c36a53c3936a5b527ac46a00c36a57c36a5bc35272680f4e656f2e53746f726167652e507574616a00c36a56c36a5ac35272680f4e656f2e53746f726167652e507574616a55c36a53c3946a5c527ac46a5cc300876422006a00c36a54c37c68124e656f2e53746f726167652e44656c65746561622100616a00c36a54c36a5cc35272680f4e656f2e53746f726167652e50757461616a51c36a52c36a53c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c75660127c56b6a00527ac46a51527ac46a52527ac46a53527ac46a54527ac46a53c300a1640700006c7566616a52c3c001149e640700006c7566616a54c3682953797374656d2e457865637574696f6e456e67696e652e476574456e74727953637269707448617368619e6499003e43616e6e6f742063616c6c2066726f6d20616e6f7468657220636f6e7472616374206f6e20626568616c66206f66206f7468657220616464726573736573680f4e656f2e52756e74696d652e4c6f672953657474696e672066726f6d206164647265737320746f2063616c6c696e6753637269707448617368680f4e656f2e52756e74696d652e4c6f676a54c36a51527ac462c900616a51c3682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e675363726970744861736861876442006a00c3537c65290e6386001b4d7573742061757468656e746963617465206173206f776e657273680f4e656f2e52756e74696d652e4c6f67006c7566625200616a51c368184e656f2e52756e74696d652e436865636b5769746e6573736163300017496e73756666696369656e742070726976656c65676573680f4e656f2e52756e74696d652e4c6f67006c7566616a51c365a2126a55527ac46a52c36597126a56527ac46a00c36a55c37c680f4e656f2e53746f726167652e476574616a57527ac46a57c36a53c39f642f0012696e73756666696369656e742066756e647368124e656f2e52756e74696d652e4e6f7469667961006c7566616a51c36a52c387640700516c7566616a57c36a53c3876422006a00c36a55c37c68124e656f2e53746f726167652e44656c65746561622d00616a57c36a53c3946a58527ac46a00c36a55c36a58c35272680f4e656f2e53746f726167652e50757461616a00c36a56c37c680f4e656f2e53746f726167652e476574616a59527ac46a59c36a53c3936a5a527ac46a00c36a56c36a5ac35272680f4e656f2e53746f726167652e507574616a51c36a52c36a53c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c75660126c56b6a00527ac46a51527ac46a52527ac46a53527ac4094e455820546f6b656e6a54527ac4034e45586a55527ac4586a56527ac4070080e03779c3116a57527ac4094e455820546f6b656e6a54527ac4034e45586a55527ac4586a56527ac4070080e03779c3116a57527ac46a51c3046e616d65876409006a54c36c7566616a51c308646563696d616c73876409006a56c36c7566616a51c30673796d626f6c876409006a55c36c7566616a51c30b746f74616c537570706c79876409006a57c36c7566616a51c30962616c616e63654f66876431006a52c3c051876424006a00c36a52c300c36579107c680f4e656f2e53746f726167652e476574616c756661621a01616a51c3087472616e7366657287643f006a52c3c053876432006a00c36a52c300c36a52c351c36a52c352c36a53c3547951795672755172755379527955727552727565abfb6c75666162cd00616a51c30c7472616e7366657246726f6d87643c006a52c3c05387642f006a00c36a52c300c36a52c351c36a52c352c353795179557275517275527952795472755272756550f96c756661627f00616a51c307617070726f766587643f006a52c3c053876432006a00c36a52c300c36a52c351c36a52c352c36a53c35479517956727551727553795279557275527275655cf66c756661623300616a51c309616c6c6f77616e6365876421006a52c3c052876418006a00c36a52c300c36a52c351c3527265f3f56c756661006c7566011cc56b6a00527ac46a51527ac4070080f420e6b5006a52527ac4070080f420e6b5006a52527ac46a51c3c0519e640700006c7566616a51c300c36a53527ac46a53c3657e0b630700006c7566616a00c36a53c37c680f4e656f2e53746f726167652e476574616a54527ac46a54c368184e656f2e52756e74696d652e436865636b5769746e65737361630700006c7566616a52c36a55527ac46a53c3064d696e7465647e6a56527ac46a00c36a56c37c680f4e656f2e53746f726167652e476574616a57527ac46a57c3642d00144f776e657220616c7265616479206d696e746564680f4e656f2e52756e74696d652e4c6f67006c7566616a00c36a56c3515272680f4e656f2e53746f726167652e507574616a00c36a55c37c657c0e6a58527ac4006a54c36a55c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f746966796a54c365f20d6a59527ac46a00c36a59c37c680f4e656f2e53746f726167652e476574616a5a527ac46a5ac36a55c3936a5b527ac46a00c36a59c36a5bc35272680f4e656f2e53746f726167652e50757461516c7566012fc56b6a00527ac46a51527ac46a52527ac46a53527ac40e696e5f63697263756c6174696f6e6a54527ac4070080e03779c3116a55527ac40500e87648176a56527ac40600282e8cd1006a57527ac404a0768d5b6a58527ac404a0bc925b6a59527ac40420b1965b6a5a527ac40420f79b5b6a5b527ac4086d696e74656452316a5c527ac4086d696e74656452326a5d527ac40e696e5f63697263756c6174696f6e6a54527ac4070080e03779c3116a55527ac40500e87648176a56527ac40600282e8cd1006a57527ac404a0768d5b6a58527ac404a0bc925b6a59527ac40420b1965b6a5a527ac40420f79b5b6a5b527ac4086d696e74656452316a5c527ac4086d696e74656452326a5d527ac468134e656f2e52756e74696d652e47657454696d65616a5e527ac46a00c36a54c37c680f4e656f2e53746f726167652e476574616a5f527ac46a5fc36a51c3936a60527ac46a60c36a55c3a0640700006c7566616a5ec36a58c3a2649f006a5ec36a59c3a16495000f4d696e74696e6720526f756e642031680f4e656f2e52756e74696d652e4c6f676a52c36a5cc37e6a0111527ac46a51c36a56c3a1645d006a00c306726f756e64316a52c3527265e6056448006a00c36a0111c37c680f4e656f2e53746f726167652e4765746191642a006a53c3631f006a00c36a0111c3515272680f4e656f2e53746f726167652e5075746161516c7566616a5ec36a5ac3a2649f006a5ec36a5bc3a16495000f4d696e74696e6720726f756e642032680f4e656f2e52756e74696d652e4c6f676a52c36a5dc37e6a0112527ac46a51c36a57c3a1645d006a00c306726f756e64326a52c35272653f056448006a00c36a0112c37c680f4e656f2e53746f726167652e4765746191642a006a53c3631f006a00c36a0112c3515272680f4e656f2e53746f726167652e5075746161516c7566610c4e6f7420656c696769626c65680f4e656f2e52756e74696d652e4c6f67006c75665bc56b6a00527ac46a51527ac46a52527ac46a51c30873656e745f6e656fc300876441006a51c30873656e745f676173c30087642f00164e6f206e656f206f7220676173206174746163686564680f4e656f2e52756e74696d652e4c6f67006c7566616a51c3653e006a53527ac46a00c36a53c36a51c30673656e646572c36a52c353795179557275517275527952795472755272756596fc6a54527ac46a54c36c75665bc56b6a00527ac40480cb816e6a51527ac404407658236a52527ac40480cb816e6a51527ac404407658236a52527ac46a00c30873656e745f6e656fc36a51c3950400e1f505966a53527ac46a00c30873656e745f676173c36a52c3950400e1f505966a54527ac46a53c36a54c3936a55527ac46a55c36c7566011cc56b6a00527ac4209b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc56a51527ac420e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c606a52527ac4066c61737454586a53527ac46a00c36a53c37c680f4e656f2e53746f726167652e476574616a54527ac4682953797374656d2e457865637574696f6e456e67696e652e476574536372697074436f6e7461696e65726168174e656f2e5472616e73616374696f6e2e47657448617368616a55527ac46a54c36a55c387640700006c7566616a00c36a53c36a55c35272680f4e656f2e53746f726167652e5075746165480a6a56527ac46a00c36a56c300527265dbfd6a57527ac46a56c30673656e646572c36a58527ac46a57c36391006a56c30873656e745f6e656fc300a06435006a58c36a56c30873656e745f6e656fc36a51c3527206726566756e6454c168124e656f2e52756e74696d652e4e6f74696679616a56c30873656e745f676173c300a06435006a58c36a56c30873656e745f676173c36a52c3527206726566756e6454c168124e656f2e52756e74696d652e4e6f7469667961006c7566616a58c365f6076a59527ac46a00c36a59c37c680f4e656f2e53746f726167652e476574616a5a527ac46a56c365a6fd6a5b527ac46a5bc36a5ac3936a5c527ac46a00c36a59c36a5cc35272680f4e656f2e53746f726167652e507574616a00c36a5bc37c65ec076a5d527ac4006a58c36a5bc35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c75660114c56b6a00527ac46a51527ac41479a3f4abfb672cd9ecb56b814858e849f54bdda16a52527ac46a52c368184e656f2e52756e74696d652e436865636b5769746e65737361633b00224d7573742068617665204b594320526567697374726172207065726d697373696f6e680f4e656f2e52756e74696d652e4c6f67006c7566616a51c3c0529e642a0011696e636f727265637420617267206c656e680f4e656f2e52756e74696d652e4c6f67006c7566616a51c300c36a53527ac46a51c351c36a54527ac4006a57527ac46a54c3c06a58527ac4616a57c36a58c39f6482006a54c36a57c3c36a55527ac46a57c351936a57527ac46a53c36a55c37c65b5006a56527ac46a56c3c0012487644b006a00c36a56c3515272680f4e656f2e53746f726167652e507574616a55c3106b79635f726567697374726174696f6e52c168124e656f2e52756e74696d652e4e6f746966796281ff61006c75666279ff616161516c756659c56b6a00527ac46a51527ac46a52527ac46a51c36a52c37c6533006a53527ac46a53c3c0012487641f006a00c36a53c37c680f4e656f2e53746f726167652e476574616c756661006c756656c56b6a00527ac46a51527ac40a6b7963417070726f76656a52527ac46a52c36a00c36a51c37e7e6c756660c56b6a00527ac46a51527ac46a00c3537c656b00630700006c7566616a51c3c0529e640700006c7566616a51c300c36a52527ac46a52c365cc01630700006c7566616a51c351c36a53527ac46a53c3c00114876424006a00c36a52c36a53c35272680f4e656f2e53746f726167652e50757461516c756661006c75665dc56b6a00527ac46a51527ac46a00c3126f776e6572735f696e697469616c697a65647c680f4e656f2e53746f726167652e476574616334001b506c656173652072756e20696e697469616c697a654f776e657273680f4e656f2e52756e74696d652e4c6f67006c756661006a52527ac46a00c36573006a53527ac4006a55527ac46a53c3c06a56527ac4616a55c36a56c39f6447006a53c36a55c3c36a54527ac46a55c351936a55527ac46a54c368184e656f2e52756e74696d652e436865636b5769746e6573736164c1ff6a52c351936a52527ac462b4ff6161616a52c36a51c3a26c756654c56b6a00527ac46a00c3066f776e6572317c680f4e656f2e53746f726167652e476574616a00c3066f776e6572327c680f4e656f2e53746f726167652e476574616a00c3066f776e6572337c680f4e656f2e53746f726167652e476574616a00c3066f776e6572347c680f4e656f2e53746f726167652e476574616a00c3066f776e6572357c680f4e656f2e53746f726167652e4765746155c176c96c756656c56b6a00527ac46a00c3066f776e65723187633b006a00c3066f776e65723287632d006a00c3066f776e65723387631f006a00c3066f776e657234876311006a00c3066f776e6572358764080061516c756661006c756658c56b6a00527ac40c6f776e6572314d696e7465640c6f776e6572324d696e7465640c6f776e6572334d696e7465640c6f776e6572344d696e7465640c6f776e6572354d696e74656455c176c96a51527ac4006a54527ac46a51c36a53527ac46a53c3c06a55527ac4616a54c36a55c39f643c006a53c36a54c3c36a52527ac46a54c351936a54527ac46a00c36a52c37c680f4e656f2e53746f726167652e4765746163c6ff006c756662bfff616161516c75660116c56b6a00527ac414507dd1f00e30e7955ab8b349707f42fa2b65376b6a51527ac41451b824a566a64543759cd5c958c193afa4d0b8fb6a52527ac414993e3a81002d4b5a56ac9808ceec1fefcb2ebcf56a53527ac414edcfa803566c0600a682d6c89ab4d035e13346ba6a54527ac414e39c5a9e04751bfb85dfd0b607766cdcb995719f6a55527ac46a00c3126f776e6572735f696e697469616c697a65647c680f4e656f2e53746f726167652e476574616390016a00c3066f776e6572316a51c35272680f4e656f2e53746f726167652e507574616a00c3066f776e6572326a52c35272680f4e656f2e53746f726167652e507574616a00c3066f776e6572336a53c35272680f4e656f2e53746f726167652e507574616a00c3066f776e6572346a54c35272680f4e656f2e53746f726167652e507574616a00c3066f776e6572356a55c35272680f4e656f2e53746f726167652e507574616a00c30c6f776e6572314d696e746564005272680f4e656f2e53746f726167652e507574616a00c30c6f776e6572324d696e746564005272680f4e656f2e53746f726167652e507574616a00c30c6f776e6572334d696e746564005272680f4e656f2e53746f726167652e507574616a00c30c6f776e6572344d696e746564005272680f4e656f2e53746f726167652e507574616a00c30c6f776e6572354d696e746564005272680f4e656f2e53746f726167652e507574616a00c3126f776e6572735f696e697469616c697a6564515272680f4e656f2e53746f726167652e50757461516c756661006c756656c56b6a00527ac46a51527ac409616c6c6f77616e63656a52527ac46a52c36a00c36a51c37e7e6c756655c56b6a00527ac40762616c616e63656a51527ac46a51c36a00c37e6c756655c56b6a00527ac40e696e5f63697263756c6174696f6e6a51527ac46a00c36a51c37c680f4e656f2e53746f726167652e476574616c756659c56b6a00527ac46a51527ac40e696e5f63697263756c6174696f6e6a52527ac46a00c36a52c37c680f4e656f2e53746f726167652e476574616a53527ac46a53c36a51c3936a53527ac46a00c36a52c36a53c35272680f4e656f2e53746f726167652e50757461516c756658c56b6a00527ac40e696e5f63697263756c6174696f6e6a51527ac4070080e03779c3116a52527ac46a00c36a51c37c680f4e656f2e53746f726167652e476574616a53527ac46a52c36a53c3946a54527ac46a54c36c75665ec56b6a00527ac46a51527ac46a51c36a00c3946a52527ac46a52c3c56a53527ac4006a54527ac46a00c36a55527ac461616a00c36a51c39f6433006a54c36a55c3936a56527ac46a56c36a53c36a54c37bc46a54c351936a54527ac46a55c36a54c3936a00527ac462c8ff6161616a53c36c75660119c56b209b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc56a00527ac420e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c606a51527ac4682953797374656d2e457865637574696f6e456e67696e652e476574536372697074436f6e7461696e6572616a52527ac46a52c3681d4e656f2e5472616e73616374696f6e2e4765745265666572656e636573616a53527ac4682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e6753637269707448617368616a54527ac4006a55527ac4006a56527ac4006a57527ac4006a58527ac46a53c3c000a0649901006a5c527ac46a53c3c06a5d527ac4616a5cc36a5dc39f6474006a53c36a5cc3c36a59527ac46a5cc351936a5c527ac46a59c368184e656f2e4f75747075742e47657453637269707448617368616a54c387640c00516a58527ac462b4ff616a55c363adff6a59c368184e656f2e4f75747075742e47657453637269707448617368616a55527ac46287ff616161006a5f527ac46a52c3681a4e656f2e5472616e73616374696f6e2e4765744f757470757473616a5e527ac46a5ec3c06a60527ac4616a5fc36a60c39f64ca006a5ec36a5fc3c36a5a527ac46a5fc351936a5f527ac46a5ac368184e656f2e4f75747075742e47657453637269707448617368616a54c38764bdff6a5ac368154e656f2e4f75747075742e47657441737365744964616a00c3876425006a56c36a5ac368134e656f2e4f75747075742e47657456616c756561936a56527ac4616a5ac368154e656f2e4f75747075742e47657441737365744964616a51c3876456ff6a57c36a5ac368134e656f2e4f75747075742e47657456616c756561936a57527ac46231ff616161c76a5b527ac46a54c36a5bc30872656365697665727bc46a55c36a5bc30673656e6465727bc46a56c36a5bc30873656e745f6e656f7bc46a57c36a5bc30873656e745f6761737bc46a58c36a5bc31773656e745f66726f6d5f636f6e74726163745f616464727bc46a5bc36c7566",
                "parameters": "0710",
                "returntype": 5
            },
            "name": "NEX Token",
            "code_version": "1",
            "author": "Neon Exchange AG",
            "email": "contact@neonexchange.org",
            "description": "NEX Security Token: NEX is a platform for high performance decentralized exchange and payment",
            "properties": {
                "storage": true,
                "dynamic_invoke": false,
                "payable": true
            }
        }
    }

return to the `Default JSON-RPC Command List`_

getnewaddress
"""""""""""""

Creates a new address.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getnewaddress", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "AcDXpJmy41nYouew3axCHfTi7JkbezJTkW"
    }

Response Description:

Returns the newly created address.

return to the `Default JSON-RPC Command List`_

getrawmempool
"""""""""""""

Returns the list of unconfirmed transactions in memory.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getrawmempool", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [
            "0x765d7a6fbcad0e36c89a4c89a711e076e219fd00aa77eba815a0c3bf5330f4e5",
            "0x7225b312fa0a53f9a00aac3ef6bffc587d015f23314a88e322dd7bda9b54f022",
            "0xb2226343ed61504d160989de880b1f0c650e986cc09a6dfadde030437ecf2afb",
            "0xf9dc74ffb438a8009c62c37b75ef4f6f2330953df585135d1a99cad032a0be7b",
            "0x516b2b923547e568e33309286f154892ea8835bd590a9901b3dddb72a1513b3c",
            "0x02dadc23fc6cee9033920df3b7db530d9c99f4f59bbfa5fb4b0295d25ef83f8f",
            "0xee9fb504349a0ed0822d6028f4dfa89f0b529f52384d87f40aabc9d9fe2824c2",
            "0x96607ca0c4170c0a61f1ee5f05ed03ba1501249c46b5a88ffe9ff11cf82d4349",
            "0xb2b9a04b0dcf2b98ec750b218364af2c80ff1708a14a2a8d0f9746487b2bdb92",
            "0xeb96c8e077f1eb011db8cb01e598c95244c18572afc5e3583d14348fef64085e",
            "0xe370272613e89df623cae55a9a54a24b05e12c55592dae4957db45a87eeb7fbb",
            "0xf20a445d44fcadaba9d3f427114a725b5854953e899a90cfd45b9715047239bd",
            "0xfcf0cc117931d4f713730d4343e536d9704b8c9f7d1c205772fa22b9832c2604",
            "0xdd6ba828702ffde2afdabf16eeda73da34c77974cdc839a7c2514ebc386356bf",
            "0x69dc29c832d2a9a6058c9ea7e69477a377c6b891f0c4147adcc4732b21f4aa99",
            "0xd4b131bd3c3ae1ebf023123934e649eb068f8d2f2459a5e4fcc9bfe0a8521a3b",
            "0x40019fa3cae0bf249e9ae7e7aac6c72fd6a77aa5edc98a2fbab5cbb5c3d09aff",
            "0xb676cccbbb2e3bc865997cb9bbedf6765b91bdc28edc7490368d9adbbee9b597",
            "0x236519a7557cbede85316f51bb36260b08c1946528846a6d0214c26e61a84d09",
            "0x4c116f527793d27d9ac022ce7028198750f7b0ca4ca6dbcbb2ed195a532d818a",
            "0x5999a6368136d1034f73c4827336f812c991457e8b751edfda0cff61fed18383",
            "0x281f89f4bce17f8c051f4a7494ec764222e7d353c3a70edde8a1b53b28d08170",
            "0xb9786714aa16e49d78295f378b2dcd64b1764562f32627b6282eef98a9caf6e5",
            "0xd87fd69f21101e38467048a2dc7e3b9be1d8af71504e887043ddd17ed67b5621",
            "0x992262f283084d69bf473992344ac62463422d16c03c2fa1d8efb44309c4b1db",
            "0x3a4a924d3883275a2bf539de77ff5e989650126d48b804a810deefc9194dffc4",
            "0xe3a8dd4abac5ead609c462a157bb859c83a7543c79a616c6aa055de62c6ab5f8",
            "0x8cde571719b3f71bffc97ffee10eb20e9e47db4a689cf9f52752fef6ef60fbab",
            "0x809dda93391add90fe708817a20586c2e7ae6707cd304d0f73b46b78478b6d8b",
            "0x999fb2ce99a46d8251b6ca9dd35273e033598b1c2eb2f3bfa85d370c0e640a8f",
            "0xb180f9d3f3d70cfb2429b3882a6c348f037fe47bb56a80acd637ddb7e093c605",
            "0xcfe64fae6abb344d2a43ec99890dce29a5532ad5ba281cfce6a6b95020090251",
            "0x138b089a06aa312415b424c6ea4a7d22bceaec638c8cb19a98e649b8ea704be6",
            "0xf5f031052b0333446b37c8d37c382a76f91aa1a3409e3bd36be4f60e123dd434",
            "0x592b2a8329528777203360c6b0a078ad366df8423a3bf68a2d4bf7d6990052b2",
            "0xe67e4696c3b5b4d1cb87592150e6a4efb512e822ada63b0c1ed60e0713aa1459",
            "0x2d4dc7864456ede04372a6f51e1598d8592a2144b0f1c423e29357e00e7e7fa4",
            "0x9c6895bb32847a63c2db5129691669036da1ec9ea3286f61f9d1272a0b575d95",
            "0xa50680cc358fc923d424703d139c1d972609b476ed04a3827e240dc089ab953a",
            "0x4af03e3e889b7ecd7f2812b3d1001b74cd86769b0d6c7618a3fa6c323965e54c",
            "0x05f1fd0aa885f8db8821557edd4fa90253ab45129e7327476cba045df75aa9f0",
            "0x47760474c4e9c51f2b9200e5e24d6d33fbbcc81eac40e505ac1e3ca80805a616"
        ]
    }

Response Description:

These are the unconfirmed transactions received by the node.

return to the `Default JSON-RPC Command List`_

getrawtransaction
"""""""""""""""""

Returns the corresponding transaction information, based on the specified hash value.

Parameter Description
#####################

Txid: Transaction ID

Verbose: Optional, the default value of verbose is 0. When verbose is 0, the serialized information of the block is returned, represented by a hexadecimal string. If you need to get detailed information, you will need to use the SDK for deserialization. When verbose is 1, detailed information of the corresponding block in Json format string, is returned.

Examples
########

**Example 1: Using a specified txid, verbose=0**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getrawtransaction", 
        "params": ["f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "8000012023ba2703c53263e8d6e522dc32203339dcd8eee901ff6a846c115ef1fb88664b00aa67f2c95e9405286db1b56c9120c27c698490530000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50010a5d4e8000000affb37f5fdb9c6fec48d9f0eee85af82950f9b4a9b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500f01b9b0986230023ba2703c53263e8d6e522dc32203339dcd8eee9014140a88bd1fcfba334b06da0ce1a679f80711895dade50352074e79e438e142dc95528d04a00c579398cb96c7301428669a09286ae790459e05e907c61ab8a1191c62321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac"
    }

**Example 2: Using a specified txid, verbose=1**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getrawtransaction", 
        "params": ["f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a", 1]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "txid": "0xf999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a",
            "size": 283,
            "type": "ContractTransaction",
            "version": 0,
            "attributes": [
                {
                    "usage": 32,
                    "data": "23ba2703c53263e8d6e522dc32203339dcd8eee9"
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "10000",
                    "address": "AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9"
                },
                {
                    "n": 1,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "99990000",
                    "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                }
            ],
            "vin": [
                {
                    "txid": "0x539084697cc220916cb5b16d2805945ec9f267aa004b6688fbf15e116c846aff",
                    "vout": 0
                }
            ],
            "sys_fee": "0",
            "net_fee": "0",
            "scripts": [
                {
                    "invocation": "40a88bd1fcfba334b06da0ce1a679f80711895dade50352074e79e438e142dc95528d04a00c579398cb96c7301428669a09286ae790459e05e907c61ab8a1191c6",
                    "verification": "21031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac"
                }
            ],
            "blockhash": "0x6088bf9d3b55c67184f60b00d2e380228f713b4028b24c1719796dcd2006e417",
            "confirmations": 3082,
            "blocktime": 1533756500
        }
    }

Response Description:

When verbose = 1, the result in JSON format is returned.

return to the `Default JSON-RPC Command List`_

getstorage
""""""""""

Returns the stored value, according to the contract script hash and the stored key.

Parameter Description
#####################

script_hash: Contract script hash

key: The key to look up in storage (in hex string)

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getstorage", 
        "params": ["b9fbcff6e50fd381160b822207231233dd3c56c2", "696e5f63697263756c6174696f6e"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": "00a031a95fe300"
    }

return to the `Default JSON-RPC Command List`_

gettxout
""""""""

Returns the corresponding unspent transaction output information (returned change), based on the specified hash and index. If the transaction output is already spent, the result value will be ``null``.

Parameter Description
#####################

Txid: Transaction ID

N: The index of the transaction output to be obtained in the transaction (starts from 0)

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "gettxout", 
        "params": ["42978cd563e9e95550fb51281d9071e27ec94bd42116836f0d0141d57a346b3e", 1]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "n": 1,
            "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
            "value": "99989900",
            "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
        }
    }

return to the `Default JSON-RPC Command List`_

getpeers
""""""""

Returns the list of nodes that the node is currently connected/disconnected from.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getpeers", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "connected": [
                {
                    "address": "###.91.248.98",
                    "port": 10333
                },
                {
                    "address": "###.254.43.76",
                    "port": 10333
                },
                {
                    "address": "###.33.136.165",
                    "port": 10333
                },
                {
                    "address": "###.227.186.72",
                    "port": 10333
                },
                {
                    "address": "###.130.76.116",
                    "port": 10333
                },
                {
                    "address": "###.56.153.154",
                    "port": 10333
                },
                {
                    "address": "###.216.146.68",
                    "port": 10333
                },
                {
                    "address": "###.74.91.157",
                    "port": 10333
                },
                {
                    "address": "###.144.100.101",
                    "port": 10333
                },
                {
                    "address": "###.75.27.231",
                    "port": 10333
                },
                {
                    "address": "###.208.145.21",
                    "port": 10333
                },
                {
                    "address": "###.254.17.56",
                    "port": 10333
                }
            ],
            "unconnected": [
                {
                    "address": "###.89.188.179",
                    "port": 10333
                },
                {
                    "address": "###.157.159.215",
                    "port": 10333
                },
                {
                    "address": "###.251.27.28",
                    "port": 10333
                },
                {
                    "address": "###.210.151.2",
                    "port": 10333
                },
                {
                    "address": "###.179.19.196",
                    "port": 17333
                }
            ],
            "bad": [
                {
                    "address": "###.90.189.192",
                    "port": 10333
                }
            ]
        }
    }

Response Description:

* Connected: The nodes to which the server is currently connected.
* Unconnected: A node that is not currently connected.
* Bad: Nodes that are no longer connected.

return to the `Default JSON-RPC Command List`_

getversion
""""""""""

Returns the version information about the queried node.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getversion", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "port": 10332,
            "nonce": 4041449750,
            "useragent": "/NEO-PYTHON:0.8.2-dev/"
        }
    }

return to the `Default JSON-RPC Command List`_

getwalletheight
"""""""""""""""

Returns the current wallet index height.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getwalletheight", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 12633
    }

return to the `Default JSON-RPC Command List`_

invoke
""""""

Returns the result after calling a smart contract at scripthash with the given parameters.

.. note:: This method is to test your VM script as if they were ran on the blockchain at that point in time. This RPC call does not affect the blockchain in any way.

Parameter Description
#####################

scripthash: Smart contract scripthash

params: The parameters to be passed into the smart contract

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invoke", 
        "params": [
                "b9fbcff6e50fd381160b822207231233dd3c56c2",
                [
                    {
                        'type': str(ContractParameterType.String),
                        'value': 'name'
                    },
                    {
                        'type': str(ContractParameterType.Array),
                        'value': []
                    }
                ]
        ]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "script": "00c1046e616d6567c2563cdd3312230722820b1681d30fe5f6cffbb9",
            "state": "HALT, BREAK",
            "gas_consumed": "0.128",
            "stack": [
                {
                    "type": "ByteArray",
                    "value": "4e45582054656d706c617465205632"
                }
            ]
        }
    }

return to the `Default JSON-RPC Command List`_

invokefunction
""""""""""""""

Returns the result after calling a smart contract at scripthash with the given operation and parameters.

.. note:: This method is to test your VM script as if they were ran on the blockchain at that point in time. This RPC call does not affect the blockchain in any way.

Parameter Description
#####################

scripthash: Smart contract scripthash

operation: The operation name (string)

params: The parameters to be passed into the smart contract operation

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invokefunction", 
        "params": [
                "b9fbcff6e50fd381160b822207231233dd3c56c2",
                'balanceOf',
                [
                    {
                        'type': str(ContractParameterType.ByteArray),
                        'value': bytearray(b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9').hex()
                    }
                ]
        ]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "script": "1423ba2703c53263e8d6e522dc32203339dcd8eee951c10962616c616e63654f6667c2563cdd3312230722820b1681d30fe5f6cffbb9",
            "state": "HALT, BREAK",
            "gas_consumed": "0.357",
            "stack": [
                {
                    "type": "ByteArray",
                    "value": "00908cd476e200"
                }
            ]
        }
    }

return to the `Default JSON-RPC Command List`_

invokescript
""""""""""""

Returns the result after passing a script through the VM.

.. note:: This method is to test your VM script as if they were ran on the blockchain at that point in time. This RPC call does not affect the blockchain in any way.

Parameter Description
#####################

script: A script runnable by the VM. This is the same script that is carried in InvocationTransaction

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invokescript", 
        "params": ["00046e616d6567c2563cdd3312230722820b1681d30fe5f6cffbb9000673796d626f6c67c2563cdd3312230722820b1681d30fe5f6cffbb90008646563696d616c7367c2563cdd3312230722820b1681d30fe5f6cffbb9"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "script": "00046e616d6567c2563cdd3312230722820b1681d30fe5f6cffbb9000673796d626f6c67c2563cdd3312230722820b1681d30fe5f6cffbb90008646563696d616c7367c2563cdd3312230722820b1681d30fe5f6cffbb9",
            "state": "HALT, BREAK",
            "gas_consumed": "0.471",
            "stack": [
                {
                    "type": "ByteArray",
                    "value": "4e45582054656d706c617465205632"
                },
                {
                    "type": "ByteArray",
                    "value": "4e585432"
                },
                {
                    "type": "Integer",
                    "value": "8"
                }
            ]
        }
    }

return to the `Default JSON-RPC Command List`_

listaddress
"""""""""""

Lists all the addresses in the current wallet.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "listaddress", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [
            {
                "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3",
                "haskey": true,
                "label": null,
                "watchonly": false
            },
            {
                "address": "AcDXpJmy41nYouew3axCHfTi7JkbezJTkW",
                "haskey": true,
                "label": null,
                "watchonly": false
            }
        ]
    }

return to the `Default JSON-RPC Command List`_

sendfrom
""""""""

Transfer from the specified address to the destination address, and you can specify a change address.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Parameter Description
#####################

assetId：asset identifier

* For NEO："neo" or c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b
* For GAS："gas" or 602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7

address_from：transfering address.

address_to: destination address.

value：Transfer amount

fee：Handling fee, optional parameter, default is 0.

change_address: Change address, optional parameter, default is the first standard address in the wallet.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendfrom", 
        "params": ["neo", "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3", "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y", 1]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "txid": "0xf86687f8716dd265263ff6db05234be0da1be417225d620150406ee2462dad77",
            "size": 283,
            "type": "ContractTransaction",
            "version": 0,
            "attributes": [
                {
                    "usage": 32,
                    "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "1",
                    "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                },
                {
                    "n": 1,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "49",
                    "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                }
            ],
            "vin": [
                {
                    "txid": "0x8eccfc1b100f9cdae845e17d83e5a2eee0d1ed1a7a251eeedf578b0aea549394",
                    "vout": 1
                }
            ],
            "sys_fee": "0",
            "net_fee": "0",
            "scripts": [
                {
                    "invocation": "401c4f8b86608e056c96e82ce209f88339f20f3f38fd670d9dcf868e253a68479f5e9ca04c5504a3a319492f771d8cf1cac68bb27d901438bc328737e39ec09393",
                    "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                }
            ]
        }
    }

Response Description:

Returns the transaction details as above if the transaction was sent successfully; otherwise the transaction is failed.
If the signature is incomplete, a pending transaction is returned. If the balance is insufficient, an error message is returned.

return to the `Default JSON-RPC Command List`_

sendrawtransaction
""""""""""""""""""

Broadcasts a transaction over the NEO network.

Parameter Description
#####################

Hex: A hexadecimal string that has been serialized, after the signed transaction in the program.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendrawtransaction", 
        "params": ["8000000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000ca9a3b0000000048033b58ef547cbf54c8ee2f72a42d5b603c00af"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": true
    }

Response Description:

When the result is true, the current transaction has been successfully broadcasted to the network.
When result is false, the current transaction has failed to broadcast. There are many reasons for this, such as double spend, incomplete signature, etc.

return to the `Default JSON-RPC Command List`_

sendtoaddress
"""""""""""""

Transfers to the specified address.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Parameter Description
#####################

assetId: asset identifier

* For NEO: "neo" or c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b
* For GAS: "gas" or 602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7

address_to: destination address.

value：Transfer amount

fee：Handling fee, optional parameter, default is 0.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendtoaddress", 
        "params": ["neo", "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y", 1, 0.00000001]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "txid": "0xba98c64be8b4f1f79be7eaa2e7b325506b579105f430da6a5325596b43667c37",
            "size": 377,
            "type": "ContractTransaction",
            "version": 0,
            "attributes": [
                {
                    "usage": 32,
                    "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "1",
                    "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                },
                {
                    "n": 1,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "49",
                    "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                },
                {
                    "n": 2,
                    "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                    "value": "13.99979999",
                    "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                }
            ],
            "vin": [
                {
                    "txid": "0x8eccfc1b100f9cdae845e17d83e5a2eee0d1ed1a7a251eeedf578b0aea549394",
                    "vout": 1
                },
                {
                    "txid": "0x6a3a6dbb06f57c3890f801cbc3c86c855a6c589355b1ba22b32283c3268282fa",
                    "vout": 0
                }
            ],
            "sys_fee": "0",
            "net_fee": "1e-08",
            "scripts": [
                {
                    "invocation": "4087b03d74b10a7b88d07352968b372d30a81d6202b46abb355d1a6e6d587f637d6553611b0820a0961ee3693efe8e9adc59ae6a3df0a3e399826de8800bf8ac67",
                    "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                }
            ]
        }
    }

Response Description:

Returns the transaction details as above if the transaction was sent successfully; otherwise the transaction is failed.
If the signature is incomplete, a pending transaction is returned. If the balance is insufficient, an error message is returned.

return to the `Default JSON-RPC Command List`_

sendmany
""""""""

Bulk transfer order, and you can specify a change address.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Parameter Description
#####################

Outputs_array: Array, the data structure of each element in the array is as follows:

::

    [{
    "asset": <assetId>,
    "value": <value>,
    "address": <address_to>},
    {
    "asset": <assetId>,
    "value": <value>,
    "address": <address_to>
    }]

assetId: asset identifier

* For NEO: "neo" or c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b
* For GAS: "gas" or 602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7

address_to: destination address.

value：Transfer amount

fee：Handling fee, optional parameter, default is 0.

change_address: Change address, optional parameter, default is the first standard address in the wallet.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendmany", 
        "params": [
                [{
                "asset": "neo",
                "value": 1,
                "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"},
                {
                "asset": "gas",
                "value": 10,
                "address": "AGFdu7qUpo2NwMuVFUb1UzUUi9b9HPnhq2"
                }],
                0.00000001,
                "AcDXpJmy41nYouew3axCHfTi7JkbezJTkW"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "txid": "0x746064214b8089754d1ba6e0d6c09d3accc0ec3192fb967cab249c58f0d3decd",
            "size": 437,
            "type": "ContractTransaction",
            "version": 0,
            "attributes": [
                {
                    "usage": 32,
                    "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                }
            ],
            "vout": [
                {
                    "n": 0,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "1",
                    "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                },
                {
                    "n": 1,
                    "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                    "value": "10",
                    "address": "AGFdu7qUpo2NwMuVFUb1UzUUi9b9HPnhq2"
                },
                {
                    "n": 2,
                    "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                    "value": "49",
                    "address": "AcDXpJmy41nYouew3axCHfTi7JkbezJTkW"
                },
                {
                    "n": 3,
                    "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                    "value": "3.99979999",
                    "address": "AcDXpJmy41nYouew3axCHfTi7JkbezJTkW"
                }
            ],
            "vin": [
                {
                    "txid": "0x8eccfc1b100f9cdae845e17d83e5a2eee0d1ed1a7a251eeedf578b0aea549394",
                    "vout": 1
                },
                {
                    "txid": "0x6a3a6dbb06f57c3890f801cbc3c86c855a6c589355b1ba22b32283c3268282fa",
                    "vout": 0
                }
            ],
            "sys_fee": "0",
            "net_fee": "1e-08",
            "scripts": [
                {
                    "invocation": "4064689bd07f0491154eb8382f541ded2a1b456ea8a94c6f18e5f224a67009a9d65737ee319fe1fda307a2016a83cc470f2f0a75b5c3524645f3efd2d0343c58e8",
                    "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                }
            ]
        }
    }

Response Description:

Returns the transaction details as above if the transaction was sent successfully; otherwise the transaction is failed.
If the signature is incomplete, a pending transaction is returned. If the balance is insufficient, an error message is returned.

return to the `Default JSON-RPC Command List`_

validateaddress
"""""""""""""""

Verifies that the address is a correct NEO address.

Parameter Description
#####################

address: A 34-bit length string, such as AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3.

Examples
########

**Example 1: Exhibits a valid address**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "validateaddress", 
        "params": ["AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3",
            "isvalid": true
        }
    }

**Example 2: Exhibits an invalid address**

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "validateaddress", 
        "params": ["AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc"]
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc",
            "isvalid": false
        }
    }

return to the `Default JSON-RPC Command List`_

Extended RPC Method Details
---------------------------

getnodestate
""""""""""""

Returns the status of the node

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getnodestate", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "Progress": [
                12768,
                "/",
                12768
            ],
            "Block-cache length": 0,
            "Blocks since program start": 393,
            "Time elapsed (minutes)": 110.82084235,
            "Blocks per min": 3.5462643277769668,
            "TPS": 0.05925479835216815
        }
    }

Response Description:

* Progress: Current Height / Header Height
* Block-cache length: Current Block Cache Count
* Bocks since program start: The number of blocks that have been added to the chain since the node started.
* Time elapsed (minutes): The number of minutes the node has been running.
* Blocks per min: The number of blocks added to the chain per minute.
* TPS: The number of transactions per second the node is processing

return to the `Extended JSON-RPC Command List`_

gettxhistory
""""""""""""

Returns a list of every tx in the associated wallet in JSON format, including block_index and blocktime.

.. note:: You need to open the wallet using ``--wallet`` with the wallet path when starting ``np-api-server``.

Example
#######

Request Body:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "gettxhistory", 
        "params": []
    }

Response:

::

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": [
            {
                "txid": "0x42978cd563e9e95550fb51281d9071e27ec94bd42116836f0d0141d57a346b3e",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "23ba2703c53263e8d6e522dc32203339dcd8eee9"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                        "value": "100",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    },
                    {
                        "n": 1,
                        "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                        "value": "99989900",
                        "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                    }
                ],
                "vin": [
                    {
                        "txid": "0xf999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a",
                        "vout": 1
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "409de3099edc1c4f62cd61109f2c8df5f5ad435f60b84ba5d811de1d19ee3c35bc054881577d230d1ba9b2a530b3260c36586216b63f018266cdf2f14477328221",
                        "verification": "21031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac"
                    }
                ],
                "block_index": 12225,
                "blocktime": 1536779693
            },
            {
                "txid": "0x5366ca28713b3f7f7be5fa99e3ecb06bbe074d333002d9b63dc08d1f09e41ec4",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "23ba2703c53263e8d6e522dc32203339dcd8eee9"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "10",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    },
                    {
                        "n": 1,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "23993.9997",
                        "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                    }
                ],
                "vin": [
                    {
                        "txid": "0xe4420094e62e2190a2e92c844437236e664d91d219626227498228cddcb7bf19",
                        "vout": 1
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "40317c06e5f93d9a56c779d19211516d8eaa80d186383b0ac578c58d8f0ff930f0459364f86b73e6f342421beb419b93a0fd4dbd7cc5a14eaaec6f96e42f4acc1b",
                        "verification": "21031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac"
                    }
                ],
                "block_index": 12245,
                "blocktime": 1536780063
            },
            {
                "txid": "0x6c177a46db501eb46bbe28645e552a2b88b650a22b035c90d9d285b88845f7a9",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "3",
                        "address": "AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm"
                    },
                    {
                        "n": 1,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "7",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0x5366ca28713b3f7f7be5fa99e3ecb06bbe074d333002d9b63dc08d1f09e41ec4",
                        "vout": 0
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "4076fc50209dd9f34d5212e50a92c93fef8a1e9e983b12004bccd92bf16bf75ae04e2ee12aee38fb1da56cbc0f51c20a7eae0542e633b8bd3ac2b606f54281abd2",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "block_index": 12258,
                "blocktime": 1536780295
            },
            {
                "txid": "0x8eccfc1b100f9cdae845e17d83e5a2eee0d1ed1a7a251eeedf578b0aea549394",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                        "value": "50",
                        "address": "AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm"
                    },
                    {
                        "n": 1,
                        "asset": "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b",
                        "value": "50",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0x42978cd563e9e95550fb51281d9071e27ec94bd42116836f0d0141d57a346b3e",
                        "vout": 0
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "40b3a41b1ffbf0920fe5c2771dcc6bd73dedd756ff8c0d4b43d4bb8dffda159a683620439fcd5294d8acc646e72abc036ffca2ade599330ef494aaa05ff378ead1",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "block_index": 12261,
                "blocktime": 1536780351
            },
            {
                "txid": "0xf84a931b3bd8aa861171d5eb56ba07059cbd92bb533a23b9a9ff2ca9cf82b4c4",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "3",
                        "address": "AZiE7xfyJALW7KmADWtCJXGGcnduYhGiCX"
                    },
                    {
                        "n": 1,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "4",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0x6c177a46db501eb46bbe28645e552a2b88b650a22b035c90d9d285b88845f7a9",
                        "vout": 1
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "40944fde42d6aa6174a7ed719adfcf4bdc1bb9e7b4b74e1de9e18c50998aff518c2f59bf52d786cc2e7509280390457fff608d71d1b419f5ebd4d3907462515c4b",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "block_index": 12265,
                "blocktime": 1536780428
            },
            {
                "txid": "0x96e3c1105f48856af32a8ce7221463ee4a4a5b2159ac127ce6bc2fe6065eb426",
                "size": 283,
                "type": "ContractTransaction",
                "version": 0,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "23ba2703c53263e8d6e522dc32203339dcd8eee9"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "500",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    },
                    {
                        "n": 1,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "23493.9997",
                        "address": "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
                    }
                ],
                "vin": [
                    {
                        "txid": "0x5366ca28713b3f7f7be5fa99e3ecb06bbe074d333002d9b63dc08d1f09e41ec4",
                        "vout": 1
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [
                    {
                        "invocation": "404378761f2a130698f84f528973948f4ef7d3d48485052cb0e019b29d126afe8d112ca14d31ae2af85ab4c6617d5d182e0f731dadb4f50d4c1aace0db737f4133",
                        "verification": "21031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac"
                    }
                ],
                "block_index": 12311,
                "blocktime": 1536781286
            },
            {
                "txid": "0x97d61b63cfdf9771c60e0a81983f18ec2a7ebfdd3a3e35529ec04ea20676e771",
                "size": 5320,
                "type": "InvocationTransaction",
                "version": 1,
                "attributes": [],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "14",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0xf84a931b3bd8aa861171d5eb56ba07059cbd92bb533a23b9a9ff2ca9cf82b4c4",
                        "vout": 1
                    },
                    {
                        "txid": "0x96e3c1105f48856af32a8ce7221463ee4a4a5b2159ac127ce6bc2fe6065eb426",
                        "vout": 0
                    }
                ],
                "sys_fee": "4.9e-06",
                "net_fee": "489.9999951",
                "scripts": [
                    {
                        "invocation": "40c2f05948bc0df8c2ebe6c1feb0f638f34a571b02c3e967b8a84d3e6ef7cccd705bed464f9f1287dbd04d8923beb736238d17833690541f9cef6f42e6d4cba65e",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "script": "0c69636f5f74656d706c6174650005646175545404746573741474657374204e45582054656d706c61746520563451550207104e8c1300000124c56b6a00527ac46a51527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a52527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a52527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a52527ac468164e656f2e53746f726167652e476574436f6e74657874616a53527ac4046e616d650673796d626f6c08646563696d616c730b746f74616c537570706c790962616c616e63654f66087472616e736665720c7472616e7366657246726f6d07617070726f766509616c6c6f77616e636559c176c96a54527ac468164e656f2e52756e74696d652e47657454726967676572616a55527ac46a55c30100876448006a52c368184e656f2e52756e74696d652e436865636b5769746e657373616a56527ac46a56c3640700516c756661651f106a57527ac46a53c36a57c351527265b90b6c7566616a55c3011087644801006a59527ac46a54c3c06a5a527ac4616a59c36a5ac39f6437006a54c36a59c3c36a58527ac46a59c351936a59527ac46a00c36a58c38764d8ff6a53c36a00c36a51c3527265d6076c756662c4ff6161616a00c3066465706c6f798764090065eb006c7566616a00c30b63697263756c6174696f6e87640c006a53c365850e6c7566616a00c30a6d696e74546f6b656e7387640c006a53c365950b6c7566616a00c31263726f776473616c655f7265676973746572876410006a53c36a51c37c65d10c6c7566616a00c31063726f776473616c655f737461747573876410006a53c36a51c37c65520c6c7566616a00c31363726f776473616c655f617661696c61626c6587640c006a53c3659a0e6c7566616a00c30f6765745f6174746163686d656e74738764090065d50e6c75666111756e6b6e6f776e206f7065726174696f6e6c756661006c75660111c56b141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a00527ac40700a031a95fe3006a51527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a00527ac40700a031a95fe3006a51527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a00527ac40700a031a95fe3006a51527ac468164e656f2e53746f726167652e476574436f6e74657874616a52527ac46a00c368184e656f2e52756e74696d652e436865636b5769746e65737361633000174d757374206265206f776e657220746f206465706c6f79680f4e656f2e52756e74696d652e4c6f67006c7566616a52c30b696e697469616c697a65647c680f4e656f2e53746f726167652e476574616351006a52c30b696e697469616c697a6564515272680f4e656f2e53746f726167652e507574616a52c36a00c36a51c35272680f4e656f2e53746f726167652e507574616a52c36a51c37c659c0c6c756661006c756656c56b6a00527ac46a51527ac46a52527ac46a00c36a51c36a52c37e7c680f4e656f2e53746f726167652e476574616c75660114c56b6a00527ac46a51527ac46a52527ac46a53527ac46a52c3c001149e640700006c7566616a51c368184e656f2e52756e74696d652e436865636b5769746e65737361630700006c7566616a53c3009f640700006c7566616a00c36a51c37c680f4e656f2e53746f726167652e476574616a53c3a26482006a51c36a52c37e6a54527ac46a53c300876422006a00c36a54c37c68124e656f2e53746f726167652e44656c65746561622100616a00c36a54c36a53c35272680f4e656f2e53746f726167652e50757461616a51c36a52c36a53c3527207617070726f766554c168124e656f2e52756e74696d652e4e6f74696679516c756661006c75660121c56b6a00527ac46a51527ac46a52527ac46a53527ac46a53c300a1640700006c7566616a51c36a52c37e6a54527ac46a54c3c001289e640700006c7566616a00c36a54c37c680f4e656f2e53746f726167652e476574616a55527ac46a55c36a53c39f6434001b496e73756666696369656e742066756e647320617070726f766564680f4e656f2e52756e74696d652e4c6f67006c7566616a00c36a51c37c680f4e656f2e53746f726167652e476574616a56527ac46a56c36a53c39f643c0023496e73756666696369656e7420746f6b656e7320696e2066726f6d2062616c616e6365680f4e656f2e52756e74696d652e4c6f67006c7566616a00c36a52c37c680f4e656f2e53746f726167652e476574616a57527ac46a56c36a53c3946a58527ac46a57c36a53c3936a59527ac46a00c36a52c36a59c35272680f4e656f2e53746f726167652e507574616a00c36a51c36a58c35272680f4e656f2e53746f726167652e50757461117472616e7366657220636f6d706c657465680f4e656f2e52756e74696d652e4c6f676a55c36a53c3946a5a527ac46a5ac300876448001472656d6f76696e6720616c6c2062616c616e6365680f4e656f2e52756e74696d652e4c6f676a00c36a54c37c68124e656f2e53746f726167652e44656c6574656162560061237570646174696e6720616c6c6f77616e636520746f206e657720616c6c6f77616e6365680f4e656f2e52756e74696d652e4c6f676a00c36a54c36a5ac35272680f4e656f2e53746f726167652e50757461616a51c36a52c36a53c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c7566011dc56b6a00527ac46a51527ac46a52527ac46a53527ac46a53c300a1640700006c7566616a52c3c001149e640700006c7566616a51c368184e656f2e52756e74696d652e436865636b5769746e65737361644f016a00c36a51c37c680f4e656f2e53746f726167652e476574616a54527ac46a54c36a53c39f642b0012696e73756666696369656e742066756e6473680f4e656f2e52756e74696d652e4c6f67006c7566616a51c36a52c387642a00117472616e7366657220746f2073656c6621680f4e656f2e52756e74696d652e4c6f67516c7566616a54c36a53c3876422006a00c36a51c37c68124e656f2e53746f726167652e44656c65746561622d00616a54c36a53c3946a55527ac46a00c36a51c36a55c35272680f4e656f2e53746f726167652e50757461616a00c36a52c37c680f4e656f2e53746f726167652e476574616a56527ac46a56c36a53c3936a57527ac46a00c36a52c36a57c35272680f4e656f2e53746f726167652e507574616a51c36a52c36a53c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c7566612166726f6d2061646472657373206973206e6f74207468652074782073656e646572680f4e656f2e52756e74696d652e4c6f67006c75660121c56b6a00527ac46a51527ac46a52527ac40f4e45582054656d706c6174652056346a53527ac4044e5854346a54527ac4586a55527ac40e696e5f63697263756c6174696f6e6a56527ac46a51c3046e616d65876409006a53c36c7566616a51c308646563696d616c73876409006a55c36c7566616a51c30673796d626f6c876409006a54c36c7566616a51c30b746f74616c537570706c7987641f006a00c36a56c37c680f4e656f2e53746f726167652e476574616c7566616a51c30962616c616e63654f6687642e006a52c3c051876421006a00c36a52c300c37c680f4e656f2e53746f726167652e476574616c756661621401616a51c3087472616e7366657287643c006a52c3c05387642f006a00c36a52c300c36a52c351c36a52c352c3537951795572755172755279527954727552727565f0fc6c75666162ca00616a51c30c7472616e7366657246726f6d87643c006a52c3c05387642f006a00c36a52c300c36a52c351c36a52c352c353795179557275517275527952795472755272756538fa6c756661627c00616a51c307617070726f766587643c006a52c3c05387642f006a00c36a52c300c36a52c351c36a52c352c3537951795572755172755279527954727552727565f1f86c756661623300616a51c309616c6c6f77616e6365876421006a52c3c052876418006a00c36a52c300c36a52c351c35272658bf86c756661006c7566011ec56b6a00527ac46a51527ac46a52527ac46a53527ac40e696e5f63697263756c6174696f6e6a54527ac4070080c6a47e8d036a55527ac40600204aa9d1016a56527ac40338850b6a57527ac40348ac0b6a58527ac40272316a59527ac468184e656f2e426c6f636b636861696e2e476574486569676874616a5a527ac46a00c36a54c37c680f4e656f2e53746f726167652e476574616a5b527ac46a5bc36a51c3936a5c527ac46a5cc36a55c3a0640700006c7566616a5ac36a57c39f640700006c7566616a5ac36a58c3a0640700516c7566616a51c36a56c3a1645e006a52c36a59c37e6a5d527ac46a00c36a5dc37c680f4e656f2e53746f726167652e476574616a5e527ac46a5ec36329006a53c3631e006a00c36a5dc3515272680f4e656f2e53746f726167652e5075746161516c756661006c756661006c756657c56b6a00527ac46a51527ac4066b79635f6f6b6a52527ac46a52c36a51c37e6a53527ac46a00c36a53c37c680f4e656f2e53746f726167652e476574616c75665dc56b6a00527ac46a51527ac46a52527ac40500286bee006a53527ac46a51c352c30087640700006c7566616a00c36a51c351c37c658aff630700006c7566616a51c352c36a53c3950400e1f505966a54527ac46a00c36a54c36a51c351c36a52c353795179557275517275527952795472755272756509fe6a55527ac46a55c36c75660111c56b6a00527ac40500286bee006a51527ac465bd036a52527ac46a00c36a52c30052726557ff6a53527ac46a53c3633a006a52c352c300a0642b006a52c351c36a52c352c37c06726566756e6453c168124e656f2e52756e74696d652e4e6f7469667961006c7566616a00c36a52c351c37c680f4e656f2e53746f726167652e476574616a54527ac46a52c352c36a51c3950400e1f505966a55527ac46a55c36a54c3936a56527ac46a00c36a52c351c36a56c35272680f4e656f2e53746f726167652e507574616a00c36a55c37c653b026a57527ac46a52c300c36a52c351c36a55c35272087472616e7366657254c168124e656f2e52756e74696d652e4e6f74696679516c75665ac56b6a00527ac46a51527ac4066b79635f6f6b6a52527ac46a51c3c000a06435006a51c300c36a53527ac46a52c36a53c37e6a54527ac46a00c36a54c37c680f4e656f2e53746f726167652e476574616c756661006c75665fc56b6a00527ac46a51527ac4141cc9c05cefffe6cdd7b182816a9152ec218d2ec06a52527ac4066b79635f6f6b6a53527ac4006a54527ac46a52c368184e656f2e52756e74696d652e436865636b5769746e65737361649d00006a57527ac46a51c3c06a58527ac4616a57c36a58c39f6481006a51c36a57c3c36a55527ac46a57c351936a57527ac46a55c3c001148764d8ff6a53c36a55c37e6a56527ac46a00c36a56c3515272680f4e656f2e53746f726167652e507574616a55c3106b79635f726567697374726174696f6e52c168124e656f2e52756e74696d652e4e6f746966796a54c351936a54527ac4627aff6161616a54c36c75665ec56b6a00527ac46a51527ac46a51c36a00c3946a52527ac46a52c3c56a53527ac4006a54527ac46a00c36a55527ac461616a00c36a51c39f6433006a54c36a55c3936a56527ac46a56c36a53c36a54c37bc46a54c351936a54527ac46a55c36a54c3936a00527ac462c8ff6161616a53c36c756655c56b6a00527ac40e696e5f63697263756c6174696f6e6a51527ac46a00c36a51c37c680f4e656f2e53746f726167652e476574616c756659c56b6a00527ac46a51527ac40e696e5f63697263756c6174696f6e6a52527ac46a00c36a52c37c680f4e656f2e53746f726167652e476574616a53527ac46a53c36a51c3936a53527ac46a00c36a52c36a53c35272680f4e656f2e53746f726167652e50757461516c756658c56b6a00527ac40e696e5f63697263756c6174696f6e6a51527ac4070080c6a47e8d036a52527ac46a00c36a51c37c680f4e656f2e53746f726167652e476574616a53527ac46a52c36a53c3946a54527ac46a54c36c75660114c56b209b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc56a00527ac420e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c606a51527ac4682953797374656d2e457865637574696f6e456e67696e652e476574536372697074436f6e7461696e6572616a52527ac46a52c3681d4e656f2e5472616e73616374696f6e2e4765745265666572656e636573616a53527ac4682d53797374656d2e457865637574696f6e456e67696e652e476574457865637574696e6753637269707448617368616a54527ac4006a55527ac4006a56527ac4006a57527ac46a53c3c000a06438016a53c300c36a58527ac46a58c368184e656f2e4f75747075742e47657453637269707448617368616a55527ac4006a5b527ac46a52c3681a4e656f2e5472616e73616374696f6e2e4765744f757470757473616a5a527ac46a5ac3c06a5c527ac4616a5bc36a5cc39f64ca006a5ac36a5bc3c36a59527ac46a5bc351936a5b527ac46a59c368184e656f2e4f75747075742e47657453637269707448617368616a54c38764bdff6a59c368154e656f2e4f75747075742e47657441737365744964616a00c3876425006a56c36a59c368134e656f2e4f75747075742e47657456616c756561936a56527ac4616a59c368154e656f2e4f75747075742e47657441737365744964616a51c3876456ff6a57c36a59c368134e656f2e4f75747075742e47657456616c756561936a57527ac46231ff6161616a54c36a55c36a56c36a57c354c176c96c756668134e656f2e436f6e74726163742e437265617465",
                "gas": 49000000000,
                "block_index": 12317,
                "blocktime": 1536781393
            },
            {
                "txid": "0xb89443e01d071f0d026ba2abd11f0a3d670b4b34ad784a122b98ae0508faa92a",
                "size": 234,
                "type": "InvocationTransaction",
                "version": 1,
                "attributes": [],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "13.9999",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0x97d61b63cfdf9771c60e0a81983f18ec2a7ebfdd3a3e35529ec04ea20676e771",
                        "vout": 0
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0.0001",
                "scripts": [
                    {
                        "invocation": "404dbdcb44ee1502bf12cf2f838e3da71966a7d601710329bb03989a48724700bc04ba014ebecf7c1923b13914cfe093c75acd70a21cad8e6dbbb10fa7002a073f",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "script": "025b5d066465706c6f7967d3d8602814a429a91afdbaa3914884a1c90c7331",
                "gas": 0,
                "block_index": 12327,
                "blocktime": 1536781572
            },
            {
                "txid": "0x6a3a6dbb06f57c3890f801cbc3c86c855a6c589355b1ba22b32283c3268282fa",
                "size": 304,
                "type": "InvocationTransaction",
                "version": 1,
                "attributes": [
                    {
                        "usage": 32,
                        "data": "1cc9c05cefffe6cdd7b182816a9152ec218d2ec0"
                    }
                ],
                "vout": [
                    {
                        "n": 0,
                        "asset": "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7",
                        "value": "13.9998",
                        "address": "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
                    }
                ],
                "vin": [
                    {
                        "txid": "0xb89443e01d071f0d026ba2abd11f0a3d670b4b34ad784a122b98ae0508faa92a",
                        "vout": 0
                    }
                ],
                "sys_fee": "0",
                "net_fee": "0.0001",
                "scripts": [
                    {
                        "invocation": "40baf4321c14a693b46121d4ac9a77e20300659a54d95e258446584fdf8dc20da764500016557c93115ed23e98b98602fb67064926640d3dbe92afddf68781d656",
                        "verification": "2103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"
                    }
                ],
                "script": "0500e87648171408742f5c5035ac2d0b1cb49474497942757f312a141cc9c05cefffe6cdd7b182816a9152ec218d2ec053c1087472616e7366657267d3d8602814a429a91afdbaa3914884a1c90c7331",
                "gas": 0,
                "block_index": 12337,
                "blocktime": 1536781752
            }
        ]
    }

return to the `Extended JSON-RPC Command List`_
