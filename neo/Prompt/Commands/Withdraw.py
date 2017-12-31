from neo.Core.Blockchain import Blockchain
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction,Transaction
from neo.Network.NodeLeader import NodeLeader
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.SmartContract.Contract import Contract
from neo.Prompt.Utils import string_from_fixed8,get_asset_id,get_asset_amount,parse_param,get_withdraw_from_watch_only,get_arg
from neo.Prompt.Commands.Invoke import test_invoke,InvokeContract
from neo.Fixed8 import Fixed8
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Cryptography.Crypto import Crypto
from neo.Implementations.Wallets.peewee.Models import VINHold
from neo.Wallets.Coin import CoinReference
from prompt_toolkit import prompt


import json
import pdb


def PrintHolds(wallet):
    wallet.LoadHolds()

    holds = wallet._holds

    for h in holds:
        print(json.dumps(h.ToJson(), indent=4))

def DeleteHolds(wallet):
    for h in wallet._holds:
        h.delete_instance()
    print("deleted holds")

def RequestWithdrawFrom(wallet, asset_id, contract_hash, to_addr, amount, require_password=True):
    asset_type = asset_id.lower()
    if asset_type not in ['neo','gas']:
        raise Exception('please specify neo or gas to withdraw')

    readable_addr = to_addr
    asset_id = get_asset_id(wallet, asset_type)

    contract = Blockchain.Default().GetContract(contract_hash)

    shash = contract.Code.ScriptHash()

    contract_addr = Crypto.ToAddress(shash)

    to_addr = parse_param(to_addr, wallet)
    amount = get_asset_amount(amount, asset_id)

    if not shash in wallet._watch_only:
        print("Add withdrawal contract address to your watch only: import watch_addr %s " % contract_addr)
        return
    if amount < Fixed8.Zero():
        print("Cannot withdraw negative amount")
        return

    unspents = wallet.FindUnspentCoinsByAssetAndTotal(
        asset_id=asset_id, amount=amount, from_addr=shash,use_standard=False,watch_only_val=64
    )

    if len(unspents) == 0:
        print("no eligible withdrawal vins")
        return
    elif len(unspents) > 1:
        print("Only one VIN at a time for now")
        return

    balance = GetWithdrawalBalance(wallet,shash,to_addr,asset_type)

    balance_fixed8 = Fixed8(balance)
    if amount <= balance_fixed8:
        amount_bytes = bytearray(amount.value.to_bytes(8,'little'))
        data = to_addr + amount_bytes
        data = data + unspents[0].RefToBytes()

        sb = ScriptBuilder()
        sb.EmitAppCallWithOperationAndData(shash, 'withdraw_%s' % asset_type, data)

        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        if len(results) and results[0].GetBoolean() == True:
            print("OK, ask for password?")


            if require_password:
                print("\n---------------------------------------------------------------")
                print("Will make withdrawal request for %s %s from %s to %s " % (amount.ToString(), asset_type,contract_addr,readable_addr))
                print("------------------------------------------------------------------\n")

                print("Enter your password to complete this request")

                passwd = prompt("[Password]> ", is_password=True)

                if not wallet.ValidatePassword(passwd):
                    print("incorrect password")
                    return
                print("submit tx")

            result = InvokeContract(wallet,tx,fee)
            return result
    else:
        print("insufficient balance")


def GetWithdrawalBalance(wallet, contract_hash, from_addr, asset_type):
    sb = ScriptBuilder()
    sb.EmitAppCallWithOperationAndData(contract_hash, 'balance_%s' % asset_type, from_addr)

    try:
        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        return results[0].GetBigInteger()
    except Exception as e:
        print("could not get balance: %s " % e)


def PerformWithdrawTx(wallet, tx, contract_hash):

    #    print("withdraw tx 1 %s " % json.dumps(tx.ToJson(), indent=4))

    requestor_contract = wallet.GetDefaultContract()
    tx.Attributes = [
        TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash(requestor_contract.Script).Data)
    ]

    withdraw_contract_state = Blockchain.Default().GetContract(contract_hash.encode('utf-8'))

    withdraw_verification = None

    if withdraw_contract_state is not None:

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

        address = verification_contract.Address
        withdraw_verification = verification_contract

    context = ContractParametersContext(tx)
    wallet.Sign(context)

    context.Add(withdraw_verification, 0, 0)

    if context.Completed:

        tx.scripts = context.GetScripts()

        print("withdraw tx %s " % json.dumps(tx.ToJson(), indent=4))


        relayed = NodeLeader.Instance().Relay(tx)

        if relayed:
            wallet.SaveTransaction(tx)
            print("Relayed Withdrawal Tx: %s " % tx.Hash.ToString())
            return True
        else:
            print("Could not relay witdrawal tx %s " % tx.Hash.ToString())
    else:

        print("Incomplete signature")



def construct_withdrawal_tx(wallet, require_password=True):

    hold = wallet._holds[0] # type: VINHold

    scripthash_to = hold.OutputHash
    scripthash_from = hold.InputHash
    f8amount = Fixed8(hold.Amount)

    withdraw_from_watch_only = get_withdraw_from_watch_only(wallet, scripthash_from)

    if f8amount is None or scripthash_to is None or withdraw_from_watch_only is None:
        print("Could not process to or from addr or amount")
        return False

    coinRef = CoinReference(prev_hash=hold.TXHash, prev_index=hold.Index)

    requested_vins = [coinRef]


    tx,height = Blockchain.Default().GetTransaction(hold.TXHash)
    output = tx.outputs[hold.Index] # type: TransactionOutput
    assetId = output.AssetId

    asset_name = 'NEO'
    if assetId == Blockchain.SystemCoin().Hash:
        asset_name = 'Gas'

    use_vins_for_asset = [requested_vins, assetId]

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    withdraw_tx = ContractTransaction(outputs=[output])

    withdraw_constructed_tx = wallet.MakeTransaction(tx=withdraw_tx,
                                                     change_address=scripthash_from,
                                                     fee=Fixed8.Zero(),
                                                     from_addr=scripthash_from,
                                                     use_standard=False,
                                                     watch_only_val=withdraw_from_watch_only,
                                                     use_vins_for_asset=use_vins_for_asset)

#    print("withdraw contsruct %s " % withdraw_constructed_tx)
    if withdraw_constructed_tx is not None:

        if require_password:
            print("\n---------------------------------------------------------------")
            print("Will make withdrawal request for %s %s from %s to %s " % (
            f8amount.ToString(), asset_name, hold.InputAddr, hold.OutputAddr))
            print("------------------------------------------------------------------\n")

            print("Enter your password to complete this request")

            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return
            print("submit tx")

        result = PerformWithdrawTx(wallet,withdraw_constructed_tx, hold.InputHash.ToString())

