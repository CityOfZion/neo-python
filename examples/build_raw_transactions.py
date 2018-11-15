"""
    This file contains 2 examples on how to build raw transactions that can be send via the 'sendrawtransaction' RPC endpoint.

    Note that the perspective taken in these examples is that you want a light wallet like approach. This means that you will
    not have a fully synced Blockchain via neo-python and that you get certain pieces of data from external sources like the API at NEOSCAN.io

    The first example will build a Transaction for sending either NEO or GAS

    The second example will interact with a smart contract on the chain (this can be sending NEP5 tokens or simply quering data).
"""

import binascii
import hashlib
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.TX.Transaction import ContractTransaction, TransactionOutput
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.Core.CoinReference import CoinReference
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neocore.Fixed8 import Fixed8
from neocore.UInt256 import UInt256
from neocore.UInt160 import UInt160
from neocore.KeyPair import KeyPair
from neo import Blockchain
from base58 import b58decode
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Wallets.utils import to_aes_key

"""
    Example 1

    Sending NEO or GAS happens via a ContractTransaction
    For more information regarding different transaction types read point 3 of:
    http://docs.neo.org/en-us/network/network-protocol.html#data-type

    The standard ``Transaction`` looks as follows (taken from the above source)

    +------+------------+-----------+--------------------------------------------------+
    | Size |   Field    | DataType  |                   Description                    |
    +------+------------+-----------+--------------------------------------------------+
    | 1    | Type       | uint8     | Type of transaction                              |
    | 1    | Version    | uint8     | Trading version, currently 0                     |
    | ?    | -          | -         | Data specific to transaction types               |
    | ?*?  | Attributes | tx_attr[] | Additional features that the transaction has     |
    | 34*? | Inputs     | tx_in[]   | Input                                            |
    | 60*? | Outputs    | tx_out[]  | Output                                           |
    | ?*?  | Scripts    | script[]  | List of scripts used to validate the transaction |
    +------+------------+-----------+--------------------------------------------------+

"""


def example1():
    neo_asset_id = Blockchain.GetSystemShare().Hash
    gas_asset_id = Blockchain.GetSystemCoin().Hash

    source_address = "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
    source_script_hash = address_to_scripthash(source_address)

    destination_address = "Ad9A1xPbuA5YBFr1XPznDwBwQzdckAjCev"
    destination_script_hash = address_to_scripthash(destination_address)

    # Let's start with building a ContractTransaction
    # The constructor already sets the correct `Type` and `Version` fields, so we do not have to worry about that
    contract_tx = ContractTransaction()

    # Since we are building a raw transaction, we will add the raw_tx flag

    contract_tx.raw_tx = True

    # Next we can add Attributes if we want. Again the various types are described in point 4. of the main link above
    # We will add a simple "description"
    contract_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Description, data="My raw contract transaction description"))

    # The next field we will set are the inputs. The inputs neo-python expects are of the type ``CoinReference``
    # To create these inputs we will need the usual `PrevHash` and `PrevIndex` values.
    # You can get the required data by using e.g. the neoscan.io API: https://api.neoscan.io/docs/index.html#api-v1-get-3
    # The `PrevHash` field equals to neoscan's `balance.unspent[index].txid` key, and `PrevIndex` comes from `balance.unspent[index].n`
    # It is up to the transaction creator to make sure that the sum of all input ``value`` fields is equal to or bigger than the amount that's intended to be send
    # The below values are taken from data out of the `neo-test1-w.wallet` fixture wallet (a wallet neo-python uses for internal testing)
    input1 = CoinReference(prev_hash=UInt256(data=binascii.unhexlify('949354ea0a8b57dfee1e257a1aedd1e0eea2e5837de145e8da9c0f101bfccc8e')), prev_index=1)
    contract_tx.inputs = [input1]

    # Next we will create the outputs.
    # The above input has a value of 50. We will create 2 outputs.

    # 1 output for sending 3 NEO to a specific destination address
    send_to_destination_output = TransactionOutput(AssetId=neo_asset_id, Value=Fixed8.FromDecimal(3), script_hash=destination_script_hash)

    # and a second output for sending the change back to ourselves
    return_change_output = TransactionOutput(AssetId=neo_asset_id, Value=Fixed8.FromDecimal(47), script_hash=source_script_hash)

    contract_tx.outputs = [send_to_destination_output, return_change_output]

    # at this point we've build our unsigned transaction and it's time to sign it before we get the raw output that we can send to the network via RPC
    # we need to create a Wallet instance for helping us with signing
    wallet = UserWallet.Create('path', to_aes_key('mypassword'), generate_default_key=False)

    # if you have a WIF use the following
    # this WIF comes from the `neo-test1-w.wallet` fixture wallet
    private_key = KeyPair.PrivateKeyFromWIF("Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV")

    # if you have a NEP2 encrypted key use the following instead
    # private_key = KeyPair.PrivateKeyFromNEP2("NEP2 key string", "password string")

    # we add the key to our wallet
    wallet.CreateKey(private_key)

    # and now we're ready to sign
    context = ContractParametersContext(contract_tx)
    wallet.Sign(context)

    contract_tx.scripts = context.GetScripts()

    print(contract_tx.Hash.ToString())

    raw_tx = contract_tx.ToArray()

    return raw_tx

    # you can confirm that this transaction is correct by running it against our docker testnet image using the following instructions
    # docker pull cityofzion/neo-python-privnet-unittest:v0.0.1
    # docker run --rm -d --name neo-python-privnet-unittest -p 20333-20336:20333-20336/tcp -p 30333-30336:30333-30336/tcp cityofzion/neo-python-privnet-unittest:v0.0.1
    # curl -X POST http://localhost:30333 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 1, "method": "sendrawtransaction", "params": ["80000190274d792072617720636f6e7472616374207472616e73616374696f6e206465736372697074696f6e01949354ea0a8b57dfee1e257a1aedd1e0eea2e5837de145e8da9c0f101bfccc8e0100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500a3e11100000000ea610aa6db39bd8c8556c9569d94b5e5a5d0ad199b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5004f2418010000001cc9c05cefffe6cdd7b182816a9152ec218d2ec0014140dbd3cddac5cb2bd9bf6d93701f1a6f1c9dbe2d1b480c54628bbb2a4d536158c747a6af82698edf9f8af1cac3850bcb772bd9c8e4ac38f80704751cc4e0bd0e67232103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"] }'
    #
    # you should then get the following result
    # {"jsonrpc":"2.0","id":1,"result":true}
    #
    # note that the `params` value comes from `raw_tx`
    # if you want to validate that the transaction is actually persisted on the chain then you can connect to the private net with neo-python and use the cli-command:
    # `tx 41b7b47aecf8573620ae28a844107f02ec14b69a6043b27138f38ae70e70f6b7` (were the TX id comes from calling: contract_tx.Hash.ToString())


"""
    Example 2

    Interacting with a Smart contract happens via an InvocationTransaction
    For more information regarding different transaction types read point 3 of:
    http://docs.neo.org/en-us/network/network-protocol.html#data-type

    The standard ``Transaction`` looks as follows (taken from the above source)

    +------+------------+-----------+--------------------------------------------------+
    | Size |   Field    | DataType  |                   Description                    |
    +------+------------+-----------+--------------------------------------------------+
    | 1    | Type       | uint8     | Type of transaction                              |
    | 1    | Version    | uint8     | Trading version, currently 0                     |
    | ?    | -          | -         | Data specific to transaction types               |
    | ?*?  | Attributes | tx_attr[] | Additional features that the transaction has     |
    | 34*? | Inputs     | tx_in[]   | Input                                            |
    | 60*? | Outputs    | tx_out[]  | Output                                           |
    | ?*?  | Scripts    | script[]  | List of scripts used to validate the transaction |
    +------+------------+-----------+--------------------------------------------------+

"""


def example2():
    source_address = "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
    source_script_hash = address_to_scripthash(source_address)

    # start by creating a base InvocationTransaction
    # the inputs, outputs and Type do not have to be set anymore.
    invocation_tx = InvocationTransaction()

    # Since we are building a raw transaction, we will add the raw_tx flag

    invocation_tx.raw_tx = True

    # often times smart contract developers use the function ``CheckWitness`` to determine if the transaction is signed by somebody eligible of calling a certain method
    # in order to pass that check you want to add the corresponding script_hash as a transaction attribute (this is generally the script_hash of the public key you use for signing)
    # Note that for public functions like the NEP-5 'getBalance' and alike this would not be needed, but it doesn't hurt either
    invocation_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=source_script_hash))

    # next we need to build a 'script' that gets executed against the smart contract.
    # this is basically the script that calls the entry point of the contract with the necessary parameters
    smartcontract_scripthash = UInt160.ParseString("31730cc9a1844891a3bafd1aa929a4142860d8d3")
    sb = ScriptBuilder()
    # call the NEP-5 `name` method on the contract (assumes contract address is a NEP-5 token)
    sb.EmitAppCallWithOperation(smartcontract_scripthash, 'name')
    invocation_tx.Script = binascii.unhexlify(sb.ToArray())

    # at this point we've build our unsigned transaction and it's time to sign it before we get the raw output that we can send to the network via RPC
    # we need to create a Wallet instance for helping us with signing
    wallet = UserWallet.Create('path', to_aes_key('mypassword'), generate_default_key=False)

    # if you have a WIF use the following
    # this WIF comes from the `neo-test1-w.wallet` fixture wallet
    private_key = KeyPair.PrivateKeyFromWIF("Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV")

    # if you have a NEP2 encrypted key use the following instead
    # private_key = KeyPair.PrivateKeyFromNEP2("NEP2 key string", "password string")

    # we add the key to our wallet
    wallet.CreateKey(private_key)

    # and now we're ready to sign
    context = ContractParametersContext(invocation_tx)
    wallet.Sign(context)

    invocation_tx.scripts = context.GetScripts()
    raw_tx = invocation_tx.ToArray()

    return raw_tx

    # you can confirm that this transaction is correct by running it against our docker testnet image using the following instructions
    # docker pull cityofzion/neo-python-privnet-unittest:v0.0.1
    # docker run --rm -d --name neo-python-privnet-unittest -p 20333-20336:20333-20336/tcp -p 30333-30336:30333-30336/tcp cityofzion/neo-python-privnet-unittest:v0.0.1
    # curl -X POST http://localhost:30333 -H 'Content-Type: application/json' -d '{ "jsonrpc": "2.0", "id": 1, "method": "sendrawtransaction", "params": ["d1001b00046e616d6567d3d8602814a429a91afdbaa3914884a1c90c733101201cc9c05cefffe6cdd7b182816a9152ec218d2ec000000141403387ef7940a5764259621e655b3c621a6aafd869a611ad64adcc364d8dd1edf84e00a7f8b11b630a377eaef02791d1c289d711c08b7ad04ff0d6c9caca22cfe6232103cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6ac"] }'
    #
    # you should then get the following result
    # {"jsonrpc":"2.0","id":1,"result":true}
    #
    # note that the `params` value comes from `raw_tx`
    # if you want to validate that the transaction is actually persisted on the chain then you can connect to the private net with neo-python and use the cli-command:
    # `tx 1672df78b7dd21f3516fb0759518dfab29cbe106715504a59a3e12a359850397` (were the TX id comes from calling: invocation_tx.Hash.ToString())


def address_to_scripthash(address: str) -> UInt160:
    """Just a helper method"""
    AddressVersion = 23  # fixed at this point
    data = b58decode(address)
    if len(data) != 25:
        raise ValueError('Not correct Address, wrong length.')
    if data[0] != AddressVersion:
        raise ValueError('Not correct Coin Version')

    checksum_data = data[:21]
    checksum = hashlib.sha256(hashlib.sha256(checksum_data).digest()).digest()[:4]
    if checksum != data[21:]:
        raise Exception('Address format error')
    return UInt160(data=data[1:21])
