from neo.Blockchain import GetBlockchain
from neo.SmartContract.ContractParameterType import ContractParameterType, ToName
from neo.VM.ScriptBuilder import ScriptBuilder
import binascii
import json

from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.CoinState import CoinState
from neo.Core.State.SpentCoinState import SpentCoinState,SpentCoinItem
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem

from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.Witness import Witness

from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType
from neo.SmartContract.StateMachine import StateMachine

from neo.BigInteger import BigInteger

def InvokeContract(wallet, args, test=True):

#    print("invoking contract! %s %s " % (wallet, args))

    BC = GetBlockchain()

    contract = BC.GetContract(args[0])

    if contract:
        descripe_contract(contract)

        params =  args[1:] if len(args) > 1 else []

        if params[0] == 'describe':
            return

        params.reverse()

        sb = ScriptBuilder()

        for p in params:
            print("pushitng param %s " % p)

            item = parse_param(p)
            sb.push(item)

            print("Script.. %s " % sb.ToArray(cleanup=False))

        sb.EmitAppCall(contract.Code.ScriptHash().Data)
#        sb.push(binascii.hexlify(contract.Code.Script))
        print("script is %s " % sb.ToArray(cleanup=False))
        out = sb.ToArray()
        print("out %s " % out)
        test_invoke(out)
    else:

        print("Contract %s not found" % args[0])



def test_invoke(script):
    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    unspentcoins = DBCollection(bc._db, sn, DBPrefix.ST_Coin, UnspentCoinState)
    spentcoins = DBCollection(bc._db, sn, DBPrefix.ST_SpentCoin, SpentCoinState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    tx = InvocationTransaction()
    tx.scripts = [ Witness()]
    tx.Script = binascii.unhexlify(script)
    print("script is %s " % tx.Script)
    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

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
        print("SUCCESSS!!!!!!")
        if success:

            service.TestCommit()

        for item in engine.EvaluationStack.Items:
            print("evaluation item %s " % item)

    except Exception as e:
        print("COULD NOT EXECUTE %s " % e)


def descripe_contract(contract):
    print("invoking contract - %s" % contract.Name.decode('utf-8'))

    functionCode = contract.Code

    parameters = functionCode.ParameterList
    script = functionCode.Script

    method_signature = []
    for p in parameters:
        method_signature.append("{ %s } " % ToName(p))
    rettype = ToName(functionCode.ReturnType)
    print("method signature %s  -->  %s" % (' '.join(method_signature), rettype))



def parse_param(p):

    try:
        val = int(p)
        out = BigInteger(val)
        return out
    except Exception as e:
        pass

    if type(p) is str:
        return binascii.hexlify( p.encode('utf-8'))

    return p