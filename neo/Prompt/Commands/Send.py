from prompt_toolkit import prompt
import traceback

from neo.Core.Blockchain import Blockchain
from neo.Fixed8 import Fixed8
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import parse_param,get_arg
import json
from neo.Core.TX.TransactionAttribute import TransactionAttribute,TransactionAttributeUsage

def construct_and_send(prompter, wallet, arguments):
    try:
        if not wallet:
            print("please open a wallet")
            return
        if len(arguments) < 3:
            print("Not enough arguments")
            return

        to_send = get_arg(arguments)
        address_to = get_arg(arguments, 1)
        amount = get_arg(arguments, 2)
        address_from = get_arg(arguments, 3)

        assetId = None

        if to_send.lower() == 'neo':
            assetId = Blockchain.Default().SystemShare().Hash
        elif to_send.lower() == 'gas':
            assetId = Blockchain.Default().SystemCoin().Hash
        elif Blockchain.Default().GetAssetState(to_send):
            assetId = Blockchain.Default().GetAssetState(to_send).AssetId

        scripthash = wallet.ToScriptHash(address_to)
        if scripthash is None:
            print("invalid address")
            return

        f8amount = Fixed8.TryParse(amount)
        if f8amount is None:
            print("invalid amount format")
            return

        if f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
            print("incorrect amount precision")
            return

        fee = Fixed8.Zero()
        if get_arg(arguments, 3):
            fee = Fixed8.TryParse(get_arg(arguments, 3))

        output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash)
        tx = ContractTransaction(outputs=[output])
        ttx = wallet.MakeTransaction(tx=tx, change_address=None, fee=fee)

        if ttx is None:
            print("insufficient funds")
            return


        passwd = prompt("[Password]> ",
                   completer=prompter.completer,
                   is_password=True,
                   history=prompter.history,
                   get_bottom_toolbar_tokens=prompter.get_bottom_toolbar,
                   style=prompter.token_style)

        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return

        standard_contract = wallet.GetChangeAddress()
        data = standard_contract.Data
        tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                              data=data)]


        context = ContractParametersContext(tx)
        wallet.Sign(context)

        if context.Completed:

            tx.scripts = context.GetScripts()


            wallet.SaveTransaction(tx)

#            print("will send tx: %s " % json.dumps(tx.ToJson(),indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                print("Relayed Tx: %s " % tx.Hash.ToString())
            else:
                print("Could not relay tx %s " % tx.Hash.ToString())

        else:
            print("Could not sign transaction")
            return




    except Exception as e:
        print("could not send: %s " % e)
        traceback.print_stack()
        traceback.print_exc()
