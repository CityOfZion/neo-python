from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_arg, get_from_addr, get_asset_id
from neo.Prompt.Commands.Tokens import do_token_transfer, amount_from_string
from neo.Wallets.Coin import CoinState
from neo.Wallets.NEP5Token import NEP5Token
from neo.UInt256 import UInt256
from neo.Fixed8 import Fixed8

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

        to_send = get_arg(arguments)
        address_to = get_arg(arguments, 1)
        amount = get_arg(arguments, 2)

        assetId = get_asset_id(wallet, to_send)

        if assetId is None:
            print("Asset id not found")
            return False

        scripthash_to = wallet.ToScriptHash(address_to)
        if scripthash_to is None:
            print("invalid address")
            return False

        scripthash_from = None

        if from_address is not None:
            scripthash_from = wallet.ToScriptHash(from_address)

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

        context = ContractParametersContext(tx, isMultiSig=signer_contract.IsMultiSigContract)
        wallet.Sign(context)

        if context.Completed:

            tx.scripts = context.GetScripts()

            wallet.SaveTransaction(tx)

#            print("will send tx: %s " % json.dumps(tx.ToJson(),indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
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


def construct_contract_withdrawal(prompter, wallet, arguments):

    if len(arguments) < 4:
        print("not enough arguments")
        return False

    from_address = get_arg(arguments, 0)
    to_send = get_arg(arguments, 1)
    to_address = get_arg(arguments, 2)
    amount = get_arg(arguments, 3)

    assetId = get_asset_id(wallet, to_send)

    scripthash_to = wallet.ToScriptHash(to_address)
    if scripthash_to is None:
        print("invalid address")
        return False

    scripthash_from = wallet.ToScriptHash(from_address)

    f8amount = Fixed8.TryParse(amount)
    if f8amount is None:
        print("invalid amount format")
        return False

    if f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
        print("incorrect amount precision")
        return False

    withdraw_from_watch_only = 0
    # check to see if contract address is in the wallet
    wallet_contract = wallet.GetContract(scripthash_from)

    # if it is not, check to see if it in the wallet watch_addr
    if wallet_contract is None:
        if scripthash_from in wallet._watch_only:
            print("found contract in watch only")
            withdraw_from_watch_only = CoinState.WatchOnly
            wallet_contract = scripthash_from

    if wallet_contract is None:
        print("please add this contract into your wallet before withdrawing from it")
        print("Use import watch_addr {ADDR}, then rebuild your wallet")

        return False

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    withdraw_tx = InvocationTransaction(outputs=[output])
    withdraw_constructed_tx = wallet.MakeTransaction(tx=withdraw_tx,
                                                     change_address=None,
                                                     fee=Fixed8.FromDecimal(.001),
                                                     from_addr=scripthash_from,
                                                     use_standard=False,
                                                     watch_only_val=withdraw_from_watch_only)

    if withdraw_constructed_tx is not None:
        return withdraw_constructed_tx


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
