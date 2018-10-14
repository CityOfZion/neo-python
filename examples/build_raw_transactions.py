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

    source_address = "D3u1UuDJkzUCixp9UUtSSza6Rgt4F9KJqv3mPSzWopgb"
    source_script_hash = address_to_scripthash(source_address)

    destination_address = "Ad9A1xPbuA5YBFr1XPznDwBwQzdckAjCev"
    destination_script_hash = address_to_scripthash(destination_address)

    # Let's start with building a ContractTransaction
    # The constructor already sets the correct `Type` and `Version` fields, so we do not have to worry about that
    contract_tx = ContractTransaction()

    # the ContractTransaction type has no special data, so we do not have to do anything there

    # Next we can add Attributes if we want. Again the various types are described in point 4. of the main link above
    # We will add a simple "description"
    contract_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Description, data="My raw contract transaction description"))

    # The next field we will set are the inputs. The inputs neo-python expects are of the type ``CoinReference``
    # To create these inputs we will need the usual `PrevHash` and `PrevIndex` values.
    # You can get the required data by using e.g. the neoscan.io API: https://api.neoscan.io/docs/index.html#api-v1-get-3
    # The `PrevHash` field equals to neoscan's `balance.unspent[index].txid` key, and `PrevIndex` comes from `balance.unspent[index].n`
    # It is up to the transaction creator to make sure that the sum of all input ``value`` fields is equal to or bigger than the amount that's intended to be send
    # The below values are fictuous and taken from the neoscan example
    input1 = CoinReference(prev_hash=UInt256(data=binascii.unhexlify('19edc4159d2bcf4c538256b17336555b71a3a6a81ecb07493fc7fa218cbafdbd')), prev_index=787)
    contract_tx.inputs = [input1]

    # Next we will create the outputs.
    # The above input has a value of 5. We will create 2 outputs.

    # 1 output for sending 3 NEO to a specific destination address
    send_to_destination_output = TransactionOutput(AssetId=neo_asset_id, Value=Fixed8.FromDecimal(3), script_hash=destination_script_hash)

    # and a second output for sending the change back to ourselves
    return_change_output = TransactionOutput(AssetId=neo_asset_id, Value=Fixed8.FromDecimal(2), script_hash=source_script_hash)

    contract_tx.outputs = [send_to_destination_output, return_change_output]

    # at this point we've build our unsigned transaction and it's time to sign it before we get the raw output that we can send to the network via RPC
    # we need to create a Wallet instance for helping us with signing
    wallet = UserWallet.Create('path', generate_default_key=False)

    # if you have a WIF use
    private_key = KeyPair.PrivateKeyFromWIF("WIF_string")

    # if you have a NEP2 encrypted key use the following instead
    private_key = KeyPair.PrivateKeyFromNEP2("NEP2 key string", "password string")

    # we add the key to our wallet
    wallet.CreateKey(private_key)

    # and now we're ready to sign
    context = ContractParametersContext(contract_tx)
    wallet.Sign(context)

    raw = contract_tx.ToArray()
    raw_signed_transaction = raw.hex()


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
    source_address = "D3u1UuDJkzUCixp9UUtSSza6Rgt4F9KJqv3mPSzWopgb"
    source_script_hash = address_to_scripthash(source_address)

    # start by creating a base InvocationTransaction
    # the inputs, outputs and Type do not have to be set anymore.
    invocation_tx = InvocationTransaction()

    # often times smart contract developers use the function ``CheckWitness`` to determine if the transaction is signed by somebody eligible of calling a certain method
    # in order to pass that check you want to add the corresponding script_hash as a transaction attribute (this is generally the script_hash of the public key you use for signing)
    # Note that for public functions like the NEP-5 'getBalance' and alike this would not be needed, but it doesn't hurt either
    invocation_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=source_script_hash))

    # next we need to build a 'script' that gets executed against the smart contract.
    # this is basically the script that calls the entry point of the contract with the necessary parameters
    smartcontract_scripthash = UInt160.ParseString("1578103c13e39df15d0d29826d957e85d770d8c9")
    sb = ScriptBuilder()
    # call the NEP-5 `name` method on the contract (assumes contract address is a NEP-5 token)
    sb.EmitAppCallWithOperation(smartcontract_scripthash, 'name')
    invocation_tx.Script = binascii.unhexlify(sb.ToArray())

    # at this point we've build our unsigned transaction and it's time to sign it before we get the raw output that we can send to the network via RPC
    # we need to create a Wallet instance for helping us with signing
    wallet = UserWallet.Create('path', generate_default_key=False)

    # if you have a WIF use
    private_key = KeyPair.PrivateKeyFromWIF("WIF_string")

    # if you have a NEP2 encrypted key use the following instead
    private_key = KeyPair.PrivateKeyFromNEP2("NEP2 key string", "password string")

    # we add the key to our wallet
    wallet.CreateKey(private_key)

    # and now we're ready to sign
    context = ContractParametersContext(invocation_tx)
    wallet.Sign(context)

    raw = invocation_tx.ToArray()
    raw_signed_transaction = raw.hex()


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
