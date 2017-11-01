from prompt_toolkit import prompt

from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neo.Fixed8 import Fixed8
from neo.Core.TX.Transaction import TransactionOutput,TransactionInput
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Prompt.Utils import parse_param,get_arg,get_asset_id
from neo.Prompt.Commands.Invoke import TestInvokeContract,InvokeContract
from neo.Wallets.Coin import CoinState
from neo.UInt256 import UInt256
import json
import pdb

def RequestWithdraw(prompter, wallet, args):

    if not wallet:
        print("please open a wallet")
        return

    withdrawal_tx = construct_contract_withdrawal(prompt, wallet, args, fee=Fixed8.Zero(), check_holds=True)

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
    withdraw_from {CONTRACT_ADDR} {ASSET} {TO_ADDR} {AMOUNT}
    """

    if not wallet:
        print("please open a wallet")
        return

    from_address = get_arg(args,0)
    assetId = get_asset_id( get_arg(args,1))
    to_address = get_arg(args, 2)
    amount = get_arg(args, 3)

    scripthash_to = wallet.ToScriptHash(to_address)
    scripthash_from = wallet.ToScriptHash(from_address)

    contract = Blockchain.Default().GetContract(scripthash_from.ToBytes())

    requested_vins = get_contract_holds_for_address(wallet,scripthash_from,scripthash_to)

    print("requested vins %s " % requested_vins)
    

def construct_contract_withdrawal(prompter, wallet, arguments, fee=Fixed8.FromDecimal(.001), check_holds=False):

    if len(arguments) < 4:
        print("not enough arguments")
        return False

    #AG5xbb6QqHSUgDw8cHdyU73R1xy4qD7WEE neo AdMDZGto3xWozB1HSjjVv27RL3zUM8LzpV 20
    from_address = get_arg(arguments,0)
    to_send = get_arg(arguments,1)
    to_address = get_arg(arguments, 2)
    amount = get_arg(arguments, 3)

    assetId = get_asset_id(to_send)

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


    withdraw_from_watch_only=0
    #check to see if contract address is in the wallet
    wallet_contract = wallet.GetContract(scripthash_from)

    #if it is not, check to see if it in the wallet watch_addr
    if wallet_contract is None:
        if scripthash_from in wallet._watch_only:
            withdraw_from_watch_only = CoinState.WatchOnly
            wallet_contract = scripthash_from

    if wallet_contract is None:
        print("please add this contract into your wallet before withdrawing from it")
        print("Use import watch_addr {ADDR}, then rebuild your wallet")

        return False

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    withdraw_tx = InvocationTransaction(outputs=[output])

    exclude_vin = None

    if check_holds:

        exclude_vin = lookup_contract_holds(wallet, scripthash_from)


    withdraw_constructed_tx = wallet.MakeTransaction(tx=withdraw_tx,
                                                     change_address=scripthash_from,
                                                     fee=  fee,
                                                     from_addr=scripthash_from,
                                                     use_standard=False,
                                                     watch_only_val=withdraw_from_watch_only,
                                                     exclude_vin=exclude_vin)

    if withdraw_constructed_tx is not None:
        return withdraw_constructed_tx




def get_contract_holds_for_address(wallet, contract_hash, addr):

    invoke_args = [contract_hash.ToString(), parse_param('getHold'), [addr.Data]]

    tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

    if tx is not None and len(results) > 0:
        holds = results[0].GetByteArray()
        holdlen = len(holds)
        numholds =  int( holdlen/33)
        vins = []
        for i in range(0, numholds):
            hstart = i*33
            hend = hstart + 33
            item = holds[hstart:hend]

            vin_index = item[0]
            vin_tx_id = UInt256(data=item[1:])

            t_input = TransactionInput(prevHash=vin_tx_id,prevIndex=vin_index)

            vins.append(t_input)

        return vins

    raise Exception("Could not lookup contract holds")


def lookup_contract_holds(wallet, contract_hash):

    print("contract hash %s " % contract_hash)
    contract = Blockchain.Default().GetContract( contract_hash.ToBytes())

    print("contract: %s " % contract)

    invoke_args = [contract_hash.ToString(), parse_param('getAllHolds'), []]

    tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

    if tx is not None and len(results) > 0:
        print("results!!! %s " % results)

        holds = results[0].GetByteArray()
        holdlen = len(holds)
        numholds =  int( holdlen/33)
        print("holds, holdlen, numholds %s %s " % (holds, numholds))
        vins = []
        for i in range(0, numholds):
            hstart = i*33
            hend = hstart + 33
            item = holds[hstart:hend]

            vin_index = item[0]
            vin_tx_id = UInt256(data=item[1:])
            print("VIN INDEX, VIN TX ID: %s %s" % (vin_index,vin_tx_id))

            t_input = TransactionInput(prevHash=vin_tx_id,prevIndex=vin_index)

            print("found tinput: %s " % json.dumps(t_input.ToJson(), indent=4))

            vins.append(t_input)


        return vins

    raise Exception("Could not lookup contract holds")