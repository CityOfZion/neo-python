from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_arg, get_from_addr, get_asset_id, lookup_addr_str, get_tx_attr_from_args
from neo.Prompt.Commands.Tokens import do_token_transfer, amount_from_string
from neo.Wallets.NEP5Token import NEP5Token
from neocore.UInt256 import UInt256
from neocore.Fixed8 import Fixed8
import pdb
import json
from prompt_toolkit import prompt
import traceback


def construct_and_send(prompter, wallet, arguments, prompt_password=True):
    try:
        if not wallet:
            print("please open a wallet")
            return False
        if len(arguments) < 3:
            print("Not enough arguments")
            return False

        arguments, from_address = get_from_addr(arguments)
        arguments, user_tx_attributes = get_tx_attr_from_args(arguments)

        to_send = get_arg(arguments)
        address_to = get_arg(arguments, 1)
        amount = get_arg(arguments, 2)

        assetId = get_asset_id(wallet, to_send)

        if assetId is None:
            print("Asset id not found")
            return False

        scripthash_to = lookup_addr_str(wallet, address_to)
        if scripthash_to is None:
            print("invalid address")
            return False

        scripthash_from = None

        if from_address is not None:
            scripthash_from = lookup_addr_str(wallet, from_address)

        # if this is a token, we will use a different
        # transfer mechanism
        if type(assetId) is NEP5Token:
            return do_token_transfer(assetId, wallet, from_address, address_to, amount_from_string(assetId, amount), prompt_passwd=prompt_password)

        f8amount = Fixed8.TryParse(amount, require_positive=True)
        if f8amount is None:
            print("invalid amount format")
            return False

        if type(assetId) is UInt256 and f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
            print("incorrect amount precision")
            return False

        fee = Fixed8.Zero()

        output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
        tx = ContractTransaction(outputs=[output])

        ttx = wallet.MakeTransaction(tx=tx,
                                     change_address=None,
                                     fee=fee,
                                     from_addr=scripthash_from)

        if ttx is None:
            print("insufficient funds")
            return False

        if prompt_password:
            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return False

        standard_contract = wallet.GetStandardAddress()

        if scripthash_from is not None:
            signer_contract = wallet.GetContract(scripthash_from)
        else:
            signer_contract = wallet.GetContract(standard_contract)

        if not signer_contract.IsMultiSigContract:

            data = standard_contract.Data
            tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                  data=data)]

        # insert any additional user specified tx attributes
        tx.Attributes = tx.Attributes + user_tx_attributes

        context = ContractParametersContext(tx, isMultiSig=signer_contract.IsMultiSigContract)
        wallet.Sign(context)

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


def parse_and_sign(prompter, wallet, jsn):

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
