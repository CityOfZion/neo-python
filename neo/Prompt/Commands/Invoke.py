from neo.Blockchain import GetBlockchain
from neo.SmartContract.ContractParameterType import ContractParameterType, ToName
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.InteropService import InteropInterface
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import parse_param,get_asset_attachments
from neo.Core.TX.Transaction import Transaction

import binascii


from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neo.Core.State.AccountState import AccountState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem

from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute,TransactionAttributeUsage
from neo.Core.TX.Transaction import TransactionOutput

from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType
from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Cryptography.Crypto import Crypto
from neo.Fixed8 import Fixed8

from neo.Core.Blockchain import Blockchain

from neo.VM.OpCode import *
from neo.BigInteger import BigInteger
import traceback
import pdb
import pdb
import json

def InvokeContract(wallet, tx):


    wallet_tx = wallet.MakeTransaction(tx=tx)

    if wallet_tx:

        context = ContractParametersContext(wallet_tx)

        wallet.Sign(context)

        if context.Completed:

            wallet_tx.scripts = context.GetScripts()

            wallet.SaveTransaction(wallet_tx)

            relayed = NodeLeader.Instance().Relay(wallet_tx)

            if relayed:
                print("Relayed Tx: %s " % tx.Hash.ToString())
                return True
            else:
                print("Could not relay tx %s " % tx.Hash.ToString())
        else:

            print("Incomplete signature")

    else:
        print("Insufficient funds")

    return False

def TestInvokeContract(wallet, args):

    BC = GetBlockchain()

    contract = BC.GetContract(args[0])

    if contract:
        descripe_contract(contract)

        verbose = False

        if 'verbose' in args:
            verbose = True
            args.remove('verbose')

#
        params =  args[1:] if len(args) > 1 else []

        if len(params) > 0 and params[0] == 'describe':
            return


        params,neo_to_attach,gas_to_attach = get_asset_attachments(params)

        params.reverse()

        sb = ScriptBuilder()

        for p in params:

            item = parse_param(p)

            if type(item) is list:
                item.reverse()
                listlength = len(item)
                for listitem in item:
                    sb.push(listitem)
                sb.push(listlength)
                sb.Emit(PACK)
            else:
                sb.push(item)


        sb.EmitAppCall(contract.Code.ScriptHash().Data)

        out = sb.ToArray()

        outputs = []

        if neo_to_attach:

            output = TransactionOutput(AssetId=Blockchain.SystemShare().Hash,
                                       Value=neo_to_attach,
                                       script_hash=contract.Code.ScriptHash(),
                                       )
            outputs.append(output)

        if gas_to_attach:

            output = TransactionOutput(AssetId=Blockchain.SystemCoin().Hash,
                                      Value=gas_to_attach,
                                      script_hash=contract.Code.ScriptHash())

            outputs.append(output)

        return test_invoke(out, wallet, outputs)

    else:

        print("Contract %s not found" % args[0])

    return None,None




def test_invoke(script, wallet, outputs):

#    print("invoke script %s " % script)

    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    tx = InvocationTransaction()
    tx.Version = 1
    tx.outputs = outputs
    tx.inputs = []
    tx.scripts = []
    tx.Script = binascii.unhexlify(script)

    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

    if len(outputs) < 1:
        contract = wallet.GetDefaultContract()
        tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash( contract.Script).Data)]

    wallet_tx = wallet.MakeTransaction(tx=tx)

    if wallet_tx:

        context = ContractParametersContext(wallet_tx)
        wallet.Sign(context)
        if context.Completed:
            wallet_tx.scripts = context.GetScripts()

    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=wallet_tx,
        table=script_table,
        service=service,
        gas=wallet_tx.Gas,
        testMode=True
    )

    engine.LoadScript(wallet_tx.Script, False)


    try:
        # drum roll?
        success = engine.Execute()

        if success:

            service.TestCommit()

            if len(service.notifications) > 0:
                for n in service.notifications:
                    Blockchain.Default().OnNotify(n)

            consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
            consumed.value = int(consumed.value)

            if consumed < Fixed8.One():
                consumed = Fixed8.One()

            #set the amount of gas the tx will need
            wallet_tx.Gas = consumed

            #reset the wallet outputs
            wallet_tx.outputs = outputs
            wallet_tx.Attributes = []

            return wallet_tx, engine.EvaluationStack.Items, engine.ops_processed
        else:
            print("error executing contract.....")
#            tx.Gas = Fixed8.One()
#            tx.Attributes = []
#            return tx, []
            return None,[]

    except Exception as e:
        print("COULD NOT EXECUTE %s " % e)

    return None,[]









def test_deploy_and_invoke(deploy_script, invoke_args, wallet):

    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    dtx = InvocationTransaction()
    dtx.Version = 1
    dtx.outputs = []
    dtx.inputs = []
    dtx.scripts = []
    dtx.Script = binascii.unhexlify(deploy_script)

    dtx = wallet.MakeTransaction(tx=dtx)
    context = ContractParametersContext(dtx)
    wallet.Sign(context)
    dtx.scripts = context.GetScripts()

    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

    contract = wallet.GetDefaultContract()
    dtx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash( contract.Script))]

    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=dtx,
        table=script_table,
        service=service,
        gas=dtx.Gas,
        testMode=True
    )

    engine.LoadScript(dtx.Script, False)

    #first we will execute the test deploy
    #then right after, we execute the test invoke

    try:
        d_success = engine.Execute()

        if d_success:

            items = engine.EvaluationStack.Items

            contract_state = None
            for i in items:
                if type(i) is ContractState:
                    contract_state = i
                    break
                elif type(i) is InteropInterface:
                    item = i.GetInterface('neo.whatever')
                    if type(item) is ContractState:
                        contract_state = item
                        break


            shash = contract_state.Code.ScriptHash()

            invoke_args, neo_to_attach, gas_to_attach = get_asset_attachments(invoke_args)

            invoke_args.reverse()

            sb = ScriptBuilder()

            # print("neo, gas %s %s " % (neo_to_attach,gas_to_attach.ToString()))

            sb = ScriptBuilder()

            for p in invoke_args:

                item = parse_param(p)

                if type(item) is list:
                    item.reverse()
                    listlength = len(item)
                    for listitem in item:
                        sb.push(listitem)
                    sb.push(listlength)
                    sb.Emit(PACK)
                else:
                    sb.push(item)

            sb.EmitAppCall(shash.Data)
            out = sb.ToArray()

            outputs = []

            if neo_to_attach:
                output = TransactionOutput(AssetId=Blockchain.SystemShare().Hash,
                                           Value=neo_to_attach,
                                           script_hash=contract_state.Code.ScriptHash(),
                                           )
                outputs.append(output)

            if gas_to_attach:
                output = TransactionOutput(AssetId=Blockchain.SystemCoin().Hash,
                                           Value=gas_to_attach,
                                           script_hash=contract_state.Code.ScriptHash())

                outputs.append(output)


            itx = InvocationTransaction()
            itx.Version = 1
            itx.outputs = outputs
            itx.inputs = []
            itx.scripts = []
            itx.Attributes = []
            itx.Script = binascii.unhexlify(out)

            if len(outputs) < 1:
                contract = wallet.GetDefaultContract()
                itx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                       data=Crypto.ToScriptHash(contract.Script).Data)]

            itx = wallet.MakeTransaction(tx=itx)
            context = ContractParametersContext(itx)
            wallet.Sign(context)
            itx.scripts = context.GetScripts()

#            print("tx: %s " % json.dumps(itx.ToJson(), indent=4))

            engine = ApplicationEngine(
                trigger_type=TriggerType.Application,
                container=itx,
                table=script_table,
                service=service,
                gas=itx.Gas,
                testMode=True
            )

            engine.LoadScript(itx.Script, False)

            i_success = engine.Execute()

            if i_success:
                service.TestCommit()

                if len(service.notifications) > 0:
                    for n in service.notifications:
                        Blockchain.Default().OnNotify(n)

                consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
                consumed.value = int(consumed.value)

                if consumed < Fixed8.One():
                    consumed = Fixed8.FromDecimal(.001)


                total_ops = engine.ops_processed

                # set the amount of gas the tx will need
                itx.Gas = consumed
                itx.Attributes = []
                result = engine.ResultsForCode(contract_state.Code)
                return itx, result, total_ops
            else:
                print("error executing invoke contract...")

        else:
            print("error executing deploy contract.....")

    except Exception as e:
        print("COULD NOT EXECUTE %s " % e)
        traceback.print_stack()
        traceback.print_exc()

    return None,[]







def descripe_contract(contract):
    print("invoking contract - %s" % contract.Name.decode('utf-8'))

