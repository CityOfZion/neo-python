from neo.Blockchain import GetBlockchain
from neo.SmartContract.ContractParameterType import ContractParameterType, ToName
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.InteropService import InteropInterface
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import parse_param

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

from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType
from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Cryptography.Crypto import Crypto
from neo.Fixed8 import Fixed8

from neo.BigInteger import BigInteger


def InvokeContract(wallet, tx):

    wallet_tx = wallet.MakeTransaction(tx=tx)

    if wallet_tx:

        context = ContractParametersContext(wallet_tx)
        wallet.Sign(context)

        if context.Completed:

            tx.scripts = context.GetScripts()

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


        params.reverse()

        sb = ScriptBuilder()

        for p in params:

            item = parse_param(p)
            sb.push(item)


        sb.EmitAppCall(contract.Code.ScriptHash().Data)

        out = sb.ToArray()

        return test_invoke(out, wallet)

    else:

        print("Contract %s not found" % args[0])

    return None,None




def test_invoke(script, wallet):

    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    tx = InvocationTransaction()
    tx.Version = 1
    tx.outputs = []
    tx.inputs = []
    tx.scripts = []
    tx.Script = binascii.unhexlify(script)
    print("testing invokeeee %s " % tx.Script)

    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

    contract = wallet.GetDefaultContract()

    tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash( contract.Script))]


    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=tx,
        table=script_table,
        service=service,
        gas=tx.Gas,
        testMode=True
    )

    engine.LoadScript(tx.Script, False)


    try:
        # drum roll?
        success = engine.Execute()

        if success:

            service.TestCommit()

            consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
            consumed.value = int(consumed.value)

            if consumed < Fixed8.One():
                consumed = Fixed8.One()

            #set the amount of gas the tx will need
            tx.Gas = consumed

            #remove the attributes that are used to add a verification script to the tx
            tx.Attributes = []

            return tx, engine.EvaluationStack.Items
        else:
            print("error executing contract.....")

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


            invoke_args.reverse()

            sb = ScriptBuilder()

            for p in invoke_args:
                item = parse_param(p)
                sb.push(item)

            sb.EmitAppCall(shash.Data)
            out = sb.ToArray()

            itx = InvocationTransaction()
            itx.Version = 1
            itx.outputs = []
            itx.inputs = []
            itx.scripts = []
            itx.Attributes = dtx.Attributes
            itx.Script = binascii.unhexlify(out)

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
                consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
                consumed.value = int(consumed.value)

                if consumed < Fixed8.One():
                    consumed = Fixed8.One()

                # set the amount of gas the tx will need
                itx.Gas = consumed

                result = engine.ResultsForCode(contract_state.Code)
                return itx, result
            else:
                print("error executing invoke contract...")

        else:
            print("error executing deploy contract.....")

    except Exception as e:
        print("COULD NOT EXECUTE %s " % e)

    return None,[]







def descripe_contract(contract):
    print("invoking contract - %s" % contract.Name.decode('utf-8'))

    functionCode = contract.Code

    parameters = functionCode.ParameterList

    method_signature = []
    for p in parameters:
        method_signature.append("{ %s } " % ToName(p))
    rettype = ToName(functionCode.ReturnType)

    print("method signature %s  -->  %s" % (' '.join(method_signature), rettype))


