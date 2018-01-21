from neo.Core.Blockchain import Blockchain
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction, Transaction
from neo.Network.NodeLeader import NodeLeader
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.SmartContract.Contract import Contract
from neo.Prompt.Utils import string_from_fixed8, get_asset_id, get_asset_amount, parse_param, get_withdraw_from_watch_only, get_arg
from neo.Prompt.Commands.Invoke import test_invoke, InvokeContract
from neocore.Fixed8 import Fixed8
from neo.VM.ScriptBuilder import ScriptBuilder
from neocore.Cryptography.Crypto import Crypto
from neo.Implementations.Wallets.peewee.Models import VINHold
from neo.Wallets.Coin import CoinReference
from prompt_toolkit import prompt
from twisted.internet import reactor

import json
import pdb


def PrintHolds(wallet):
    wallet.LoadHolds()

    holds = wallet._holds

    for h in holds:
        print(json.dumps(h.ToJson(), indent=4))
    if len(holds) == 0:
        print("No Holds to show")


def DeleteHolds(wallet, index_to_delete):
    wallet.LoadHolds()
    for index, h in enumerate(wallet._holds):
        if index_to_delete > -1:
            if index == index_to_delete:
                h.delete_instance()
        else:
            h.delete_instance()
    print("deleted hold(s)")
    wallet.LoadHolds()


def ShowCompletedHolds(wallet):
    completed = wallet.LoadCompletedHolds()
    for h in completed:
        print(json.dumps(h.ToJson(), indent=4))
    if len(completed) == 0:
        print("No Completed Holds to show")


def RequestWithdrawFrom(wallet, asset_id, contract_hash, to_addr, amount, require_password=True):
    asset_type = asset_id.lower()
    if asset_type not in ['neo', 'gas']:
        raise Exception('please specify neo or gas to withdraw')

    readable_addr = to_addr
    asset_id = get_asset_id(wallet, asset_type)

    contract = Blockchain.Default().GetContract(contract_hash)

    shash = contract.Code.ScriptHash()

    contract_addr = Crypto.ToAddress(shash)

    to_addr = parse_param(to_addr, wallet)
    amount = get_asset_amount(amount, asset_id)

    if shash not in wallet._watch_only:
        print("Add withdrawal contract address to your watch only: import watch_addr %s " % contract_addr)
        return False
    if amount < Fixed8.Zero():
        print("Cannot withdraw negative amount")
        return False

    unspents = wallet.FindUnspentCoinsByAssetAndTotal(
        asset_id=asset_id, amount=amount, from_addr=shash, use_standard=False, watch_only_val=64, reverse=True
    )

    if not unspents or len(unspents) == 0:
        print("no eligible withdrawal vins")
        return False

    balance = GetWithdrawalBalance(wallet, shash, to_addr, asset_type)

    balance_fixed8 = Fixed8(balance)
    orig_amount = amount
    if amount <= balance_fixed8:
        sb = ScriptBuilder()

        for uns in unspents:
            if amount > Fixed8.Zero():
                to_spend = amount
                if to_spend > uns.Output.Value:
                    to_spend = uns.Output.Value
                amount_bytes = bytearray(to_spend.value.to_bytes(8, 'little'))
                data = to_addr + amount_bytes
                data = data + uns.RefToBytes()
                sb.EmitAppCallWithOperationAndData(shash, 'withdraw_%s' % asset_type, data)
                amount -= uns.Output.Value

        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        for item in results:
            if not item.GetBoolean():
                print("Error performitng withdrawals")
                return False

        if require_password:
            print("\n---------------------------------------------------------------")
            print("Will make withdrawal request for %s %s from %s to %s " % (orig_amount.ToString(), asset_type, contract_addr, readable_addr))
            print("FEE IS %s " % fee.ToString())
            print("GAS IS %s " % tx.Gas.ToString())
            print("------------------------------------------------------------------\n")

            print("Enter your password to complete this request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        result = InvokeContract(wallet, tx, fee)
        return result
    else:
        print("insufficient balance")
        return False


def GetWithdrawalBalance(wallet, contract_hash, from_addr, asset_type):
    sb = ScriptBuilder()
    sb.EmitAppCallWithOperationAndData(contract_hash, 'balance_%s' % asset_type, from_addr)

    try:
        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        return results[0].GetBigInteger()
    except Exception as e:
        print("could not get balance: %s " % e)


def CleanupCompletedHolds(wallet, require_password=True):

    completed = wallet.LoadCompletedHolds()

    if len(completed) < 1:
        print("No holds to cleanup")
        return False

    sb = ScriptBuilder()
    for hold in completed:
        sb.EmitAppCallWithOperationAndData(hold.InputHash, 'cleanup_hold', hold.Vin)

    try:
        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        for i in results:
            if not i.GetBoolean():
                print("Error executing hold cleanup")
                return False

        if require_password:
            print("\n---------------------------------------------------------------")
            print("Will cleanup %s holds" % len(completed))
            print("FEE IS %s " % fee.ToString())
            print("GAS IS %s " % tx.Gas.ToString())
            print("------------------------------------------------------------------\n")

            print("Enter your password to complete this request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        result = InvokeContract(wallet, tx, fee)
        return result

    except Exception as e:
        print("could not cancel hold(s): %s " % e)
    return False


def CancelWithdrawalHolds(wallet, contract_hash, require_password=True):
    wallet.LoadHolds()
    to_cancel = []
    for hold in wallet._holds:
        if hold.FromAddress == contract_hash:
            to_cancel.append(hold)
    if len(to_cancel) < 1:
        print("No holds to cancel")
        return

    sb = ScriptBuilder()
    for hold in to_cancel:
        sb.EmitAppCallWithOperationAndData(hold.InputHash, 'cancel_hold', hold.Vin)

    try:
        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        for i in results:
            if not i.GetBoolean():
                print("Error executing hold cleanup")
                return

        if require_password:
            print("\n---------------------------------------------------------------")
            print("Will cancel %s holds" % len(to_cancel))
            print("FEE IS %s " % fee.ToString())
            print("GAS IS %s " % tx.Gas.ToString())
            print("------------------------------------------------------------------\n")

            print("Enter your password to complete this request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        result = InvokeContract(wallet, tx, fee)
        return result

    except Exception as e:
        print("could not cancel hold(s): %s " % e)


def PerformWithdrawTx(wallet, tx, contract_hash):

    requestor_contract = wallet.GetDefaultContract()
    withdraw_contract_state = Blockchain.Default().GetContract(contract_hash.encode('utf-8'))

    reedeem_script = withdraw_contract_state.Code.Script.hex()

    # there has to be at least 1 param, and the first
    # one needs to be a signature param
    param_list = bytearray(b'\x00')

    # if there's more than one param
    # we set the first parameter to be the signature param
    if len(withdraw_contract_state.Code.ParameterList) > 1:
        param_list = bytearray(withdraw_contract_state.Code.ParameterList)
        param_list[0] = 0

    verification_contract = Contract.Create(reedeem_script, param_list, requestor_contract.PublicKeyHash)

    context = ContractParametersContext(tx)
    context.Add(verification_contract, 0, bytearray(0))

    if context.Completed:

        tx.scripts = context.GetScripts()

#        print("withdraw tx %s " % json.dumps(tx.ToJson(), indent=4))

        relayed = NodeLeader.Instance().Relay(tx)

        if relayed:
            # wallet.SaveTransaction(tx) # dont save this tx
            print("Relayed Withdrawal Tx: %s " % tx.Hash.ToString())
            return tx
        else:
            print("Could not relay witdrawal tx %s " % tx.Hash.ToString())
    else:

        print("Incomplete signature")
    return False


def WithdrawAll(wallet, require_password=True):

    num_gas = 0
    num_neo = 0
    total_gas = Fixed8.Zero()
    total_neo = Fixed8.Zero()
    all_tx = []
    for hold in wallet._holds:
        f8 = Fixed8(hold.Amount)

        if hold.AssetName == 'NEO':
            num_neo += 1
            total_neo += f8
        elif hold.AssetName == 'Gas':
            num_gas += 1
            total_gas += f8

        all_tx.append(create_withdraw_tx(wallet, hold))

    if require_password:
        print("\n---------------------------------------------------------------")
        if num_gas:
            print("Will make %s request(s) for %s Gas" % (num_gas, total_gas.ToString()))
        if num_neo:
            print("Will make %s request(s) for %s NEO" % (num_neo, total_neo.ToString()))
        print("------------------------------------------------------------------\n")

        print("Enter your password to complete this request")

        passwd = prompt("[Password]> ", is_password=True)

        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return False

    later = 0
    for tx in all_tx:
        hold = tx.withdraw_hold
#        PerformWithdrawTx(wallet, tx, hold.InputHash)
        reactor.callLater(later, PerformWithdrawTx, wallet, tx, hold.InputHash.ToString())
        later += 2

    return True


def WithdrawOne(wallet, require_password=True):

    hold = wallet._holds[0]

    withdraw_tx = create_withdraw_tx(wallet, hold)

    if withdraw_tx is not None:

        if require_password:
            print("\n---------------------------------------------------------------")
            print("Will make withdrawal request for %s %s from %s to %s " % (
                Fixed8(hold.Amount).ToString(), hold.AssetName, hold.InputAddr, hold.OutputAddr))
            print("------------------------------------------------------------------\n")

            print("Enter your password to complete this request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        return PerformWithdrawTx(wallet, withdraw_tx, hold.InputHash.ToString())

    return False


def create_withdraw_tx(wallet, hold):

    f8amount = Fixed8(hold.Amount)

    coinRef = CoinReference(prev_hash=hold.TXHash, prev_index=hold.Index)

    requested_vins = [coinRef]

    use_vins_for_asset = [requested_vins, hold.AssetId]

    output = TransactionOutput(AssetId=hold.AssetId, Value=f8amount, script_hash=hold.OutputHash)
    withdraw_tx = ContractTransaction(outputs=[output])
    withdraw_tx.withdraw_hold = hold

    return wallet.MakeTransaction(tx=withdraw_tx,
                                  change_address=hold.InputHash,
                                  fee=Fixed8.Zero(),
                                  from_addr=hold.InputHash,
                                  use_standard=False,
                                  watch_only_val=64,
                                  use_vins_for_asset=use_vins_for_asset)
