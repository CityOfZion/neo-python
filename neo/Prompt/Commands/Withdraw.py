from prompt_toolkit import prompt

from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neo.Fixed8 import Fixed8
from neo.Core.TX.Transaction import TransactionOutput, TransactionInput
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Prompt.Utils import parse_param, get_arg, get_asset_id, get_asset_amount, get_withdraw_from_watch_only, parse_hold_vins
from neo.Prompt.Commands.Invoke import TestInvokeContract, InvokeContract, InvokeWithdrawTx
from neo.Wallets.Coin import CoinState
from neo.UInt256 import UInt256
import json
import pdb


def RequestWithdraw(prompter, wallet, args):

    if not wallet:
        print("please open a wallet")
        return

    withdrawal_tx = construct_contract_withdrawal_request(wallet, args, fee=Fixed8.Zero(), check_holds=True)

    if withdrawal_tx:

        # below we are going to mimic a test invoke from the prompt

        invoke_args = []

        contract_addr = args[0]
        contract_hash = Helper.AddrStrToScriptHash(contract_addr).ToString()

        # add contract hash
        invoke_args.append(contract_hash)

        # add 'withdrawRequest' method
        invoke_args.append(parse_param('withdrawalRequest'))

        invoke_args_array = []

        requestor = parse_param(args[2])
        invoke_args_array.append(requestor)

        for input in withdrawal_tx.inputs:
            invoke_args_array.append(bytearray(input.PrevHash.Data))
            invoke_args_array.append(input.PrevIndex)

        invoke_args.append(invoke_args_array)

        print("invoke args array %s " % invoke_args)

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

        if tx is not None and results is not None:
            print(
                "\n-------------------------------------------------------------------------------------------------------------------------------------")
            print("Request Withdraw successful")
            print("Total operations: %s " % num_ops)
            print("Results %s " % [str(item) for item in results])
            print("Withdraw Request gas cost: %s " % (tx.Gas.value / Fixed8.D))
            print("Withdraw Request Fee: %s " % (fee.value / Fixed8.D))
            print(
                "-------------------------------------------------------------------------------------------------------------------------------------\n")
            print("Enter your password to complete this withdrawal request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

            result = InvokeContract(wallet, tx, fee)

            return result
        else:
            print("Error testing contract invoke")
            return


def RedeemWithdraw(prompter, wallet, args):
    """
    withdraw {CONTRACT_ADDR} {ASSET} {TO_ADDR} {AMOUNT}
    """
    if not wallet:
        print("please open a wallet")
        return

    withdrawal_tx = construct_withdrawal_tx(wallet, args)

    if withdrawal_tx:

        outputs = withdrawal_tx.outputs
        contract_hash = wallet.ToScriptHash(args[0]).ToString()
        to_addr = wallet.ToScriptHash(args[2])
        invoke_args = [contract_hash, parse_param('getBalance'), [to_addr.Data]]
        print("invoke args... %s " % invoke_args)
        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)
        print("tx is %s %s" % (withdrawal_tx.outputs, withdrawal_tx.inputs))

        if tx is not None and results is not None:
            print(
                "\n-------------------------------------------------------------------------------------------------------------------------------------")
            print("Test Withdraw successful")
            print("Total operations: %s " % num_ops)
            print("Results %s " % [str(item) for item in results])
            print("Withdraw gas cost: %s " % (tx.Gas.value / Fixed8.D))
            print("Withdraw Fee: %s " % (fee.value / Fixed8.D))
            print(
                "-------------------------------------------------------------------------------------------------------------------------------------\n")
            print("Enter your password to complete this withdrawal")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return
            withdrawal_tx.scripts = []
            withdrawal_tx.Script = tx.Script
            withdrawal_tx.outputs = outputs

#            tx.scripts = []
#            tx.inputs = withdrawal_tx.inputs
#            tx.outputs = withdrawal_tx.outputs
            result = InvokeWithdrawTx(wallet, withdrawal_tx, contract_hash)

            return result
        else:
            print("Error testing contract invoke")
            return


def construct_contract_withdrawal_request(wallet, arguments, fee=Fixed8.FromDecimal(.001), check_holds=False):

    if len(arguments) < 4:
        print("not enough arguments")
        return False

    # AG5xbb6QqHSUgDw8cHdyU73R1xy4qD7WEE neo AdMDZGto3xWozB1HSjjVv27RL3zUM8LzpV 20
    from_address = get_arg(arguments, 0)
    to_send = get_arg(arguments, 1)
    to_address = get_arg(arguments, 2)
    amount = get_arg(arguments, 3)

    assetId = get_asset_id(wallet, to_send)

    f8amount = get_asset_amount(amount, assetId)

    scripthash_to = wallet.ToScriptHash(to_address)

    scripthash_from = wallet.ToScriptHash(from_address)

    withdraw_from_watch_only = get_withdraw_from_watch_only(wallet, scripthash_from)

    if f8amount is None or scripthash_to is None or withdraw_from_watch_only is None:
        print("Could not process to or from addr or amount")
        return False

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    withdraw_tx = InvocationTransaction(outputs=[output])

    exclude_vin = None

    if check_holds:

        exclude_vin = lookup_contract_holds(wallet, scripthash_from)

    withdraw_constructed_tx = wallet.MakeTransaction(tx=withdraw_tx,
                                                     change_address=scripthash_from,
                                                     fee=fee,
                                                     from_addr=scripthash_from,
                                                     use_standard=False,
                                                     watch_only_val=withdraw_from_watch_only,
                                                     exclude_vin=exclude_vin)

    if withdraw_constructed_tx is not None:
        return withdraw_constructed_tx


def construct_withdrawal_tx(wallet, args):

    from_address = get_arg(args, 0)
    assetId = get_asset_id(wallet, get_arg(args, 1))
    to_address = get_arg(args, 2)
    f8amount = get_asset_amount(get_arg(args, 3), assetId)

    scripthash_to = wallet.ToScriptHash(to_address)
    scripthash_from = wallet.ToScriptHash(from_address)

    withdraw_from_watch_only = get_withdraw_from_watch_only(wallet, scripthash_from)

    if f8amount is None or scripthash_to is None or withdraw_from_watch_only is None:
        print("Could not process to or from addr or amount")
        return False

    requested_vins = get_contract_holds_for_address(wallet, scripthash_from, scripthash_to)
    use_vins_for_asset = [requested_vins, assetId]

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    withdraw_tx = InvocationTransaction(outputs=[output])

    withdraw_constructed_tx = wallet.MakeTransaction(tx=withdraw_tx,
                                                     change_address=scripthash_from,
                                                     fee=Fixed8.FromDecimal(.001),
                                                     from_addr=scripthash_from,
                                                     use_standard=False,
                                                     watch_only_val=withdraw_from_watch_only,
                                                     use_vins_for_asset=use_vins_for_asset)

    if withdraw_constructed_tx is not None:
        return withdraw_constructed_tx


def get_contract_holds_for_address(wallet, contract_hash, addr):

    invoke_args = [contract_hash.ToString(), parse_param('getHold'), [addr.Data]]

    tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

    if tx is not None and len(results) > 0:

        vins = parse_hold_vins(results)

        return vins

    raise Exception("Could not lookup contract holds")


def lookup_contract_holds(wallet, contract_hash):

    invoke_args = [contract_hash.ToString(), parse_param('getAllHolds'), []]

    tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

    if tx is not None and len(results) > 0:

        vins = parse_hold_vins(results)

        return vins

    raise Exception("Could not lookup contract holds")
