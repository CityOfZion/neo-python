from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_arg, get_from_addr, get_asset_id, lookup_addr_str, get_tx_attr_from_args, \
    get_owners_from_params, get_fee, get_change_addr, get_asset_amount
from neo.Prompt.Commands.Tokens import do_token_transfer, amount_from_string
from neo.Prompt.Commands.Invoke import gather_signatures
from neo.Wallets.NEP5Token import NEP5Token
from neocore.UInt256 import UInt256
from neocore.Fixed8 import Fixed8
import json
from prompt_toolkit import prompt
import traceback
from logzero import logger


def construct_send_basic(wallet, arguments):
    if not wallet:
        print("please open a wallet")
        return False
    if len(arguments) < 3:
        print("Not enough arguments")
        return False

    arguments, from_address = get_from_addr(arguments)
    arguments, priority_fee = get_fee(arguments)
    arguments, user_tx_attributes = get_tx_attr_from_args(arguments)
    arguments, owners = get_owners_from_params(arguments)
    to_send = get_arg(arguments)
    address_to = get_arg(arguments, 1)
    amount = get_arg(arguments, 2)

    assetId = get_asset_id(wallet, to_send)
    if assetId is None:
        print("Asset id not found")
        return False

    scripthash_to = lookup_addr_str(wallet, address_to)
    if scripthash_to is None:
        logger.debug("invalid address")
        return False

    scripthash_from = None
    if from_address is not None:
        scripthash_from = lookup_addr_str(wallet, from_address)
        if scripthash_from is None:
            logger.debug("invalid address")
            return False

    # if this is a token, we will use a different
    # transfer mechanism
    if type(assetId) is NEP5Token:
        return do_token_transfer(assetId, wallet, from_address, address_to, amount_from_string(assetId, amount), tx_attributes=user_tx_attributes)

    f8amount = get_asset_amount(amount, assetId)
    if f8amount is False:
        logger.debug("invalid amount")
        return False
    if float(amount) == 0:
        print("amount cannot be 0")
        return False

    fee = Fixed8.Zero()
    if priority_fee is not None:
        fee = priority_fee
        if fee is False:
            logger.debug("invalid fee")
            return False

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    contract_tx = ContractTransaction(outputs=[output])
    return [contract_tx, scripthash_from, fee, owners, user_tx_attributes]


def construct_send_many(wallet, arguments):
    if not wallet:
        print("please open a wallet")
        return False
    if len(arguments) is 0:
        print("Not enough arguments")
        return False

    outgoing = get_arg(arguments, convert_to_int=True)
    if outgoing is None:
        print("invalid outgoing number")
        return False
    if outgoing < 1:
        print("outgoing number must be >= 1")
        return False

    arguments, from_address = get_from_addr(arguments)
    arguments, change_address = get_change_addr(arguments)
    arguments, priority_fee = get_fee(arguments)
    arguments, owners = get_owners_from_params(arguments)
    arguments, user_tx_attributes = get_tx_attr_from_args(arguments)

    output = []
    for i in range(outgoing):
        print('Outgoing Number ', i + 1)
        to_send = prompt("Asset to send: ")
        assetId = get_asset_id(wallet, to_send)
        if assetId is None:
            print("Asset id not found")
            return False
        if type(assetId) is NEP5Token:
            print('Sendmany does not support NEP5 tokens')
            return False
        address_to = prompt("Address to: ")
        scripthash_to = lookup_addr_str(wallet, address_to)
        if scripthash_to is None:
            logger.debug("invalid address")
            return False
        amount = prompt("Amount to send: ")
        f8amount = get_asset_amount(amount, assetId)
        if f8amount is False:
            logger.debug("invalid amount")
            return False
        if float(amount) == 0:
            print("amount cannot be 0")
            return False
        tx_output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
        output.append(tx_output)
    contract_tx = ContractTransaction(outputs=output)

    scripthash_from = None

    if from_address is not None:
        scripthash_from = lookup_addr_str(wallet, from_address)
        if scripthash_from is None:
            logger.debug("invalid address")
            return False

    scripthash_change = None

    if change_address is not None:
        scripthash_change = lookup_addr_str(wallet, change_address)
        if scripthash_change is None:
            logger.debug("invalid address")
            return False

    fee = Fixed8.Zero()
    if priority_fee is not None:
        fee = priority_fee
        if fee is False:
            logger.debug("invalid fee")
            return False

    print("sending with fee: %s " % fee.ToString())
    return [contract_tx, scripthash_from, scripthash_change, fee, owners, user_tx_attributes]


def process_transaction(wallet, contract_tx, scripthash_from=None, scripthash_change=None, fee=None, owners=None, user_tx_attributes=None):
    try:
        tx = wallet.MakeTransaction(tx=contract_tx,
                                    change_address=scripthash_change,
                                    fee=fee,
                                    from_addr=scripthash_from)

        if tx is None:
            logger.debug("insufficient funds")
            return False

        # password prompt
        passwd = prompt("[Password]> ", is_password=True)
        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return False

        standard_contract = wallet.GetStandardAddress()

        if scripthash_from is not None:
            signer_contract = wallet.GetContract(scripthash_from)
        else:
            signer_contract = wallet.GetContract(standard_contract)

        if not signer_contract.IsMultiSigContract and owners is None:

            data = standard_contract.Data
            tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                  data=data)]

        # insert any additional user specified tx attributes
        tx.Attributes = tx.Attributes + user_tx_attributes

        if owners:
            owners = list(owners)
            for owner in owners:
                tx.Attributes.append(
                    TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))

        context = ContractParametersContext(tx, isMultiSig=signer_contract.IsMultiSigContract)
        wallet.Sign(context)

        if owners:
            owners = list(owners)
            gather_signatures(context, tx, owners)

        if context.Completed:

            tx.scripts = context.GetScripts()

#            print("will send tx: %s " % json.dumps(tx.ToJson(),indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                wallet.SaveTransaction(tx)

                print("Relayed Tx: %s " % tx.Hash.ToString())
                return tx
            else:

                print("Could not relay tx %s " % tx.Hash.ToString())

        else:
            print("Transaction initiated, but the signature is incomplete")
            print(json.dumps(context.ToJson(), separators=(',', ':')))
            return False

    except Exception as e:
        print("could not send: %s " % e)
        traceback.print_stack()
        traceback.print_exc()

    return False


def parse_and_sign(wallet, jsn):

    try:
        context = ContractParametersContext.FromJson(jsn)
        if context is None:
            print("Failed to parse JSON")
            return

        wallet.Sign(context)

        if context.Completed:

            print("Signature complete, relaying...")

            tx = context.Verifiable
            tx.scripts = context.GetScripts()

            wallet.SaveTransaction(tx)

            print("will send tx: %s " % json.dumps(tx.ToJson(), indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                print("Relayed Tx: %s " % tx.Hash.ToString())
            else:
                print("Could not relay tx %s " % tx.Hash.ToString())
            return
        else:
            print("Transaction initiated, but the signature is incomplete")
            print(json.dumps(context.ToJson(), separators=(',', ':')))
            return

    except Exception as e:
        print("could not send: %s " % e)
        traceback.print_stack()
        traceback.print_exc()
