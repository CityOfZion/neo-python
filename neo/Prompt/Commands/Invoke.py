import binascii
import json
from neo.Blockchain import GetBlockchain
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.InteropService import InteropInterface
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import parse_param, get_asset_attachments, lookup_addr_str, get_owners_from_params

from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neo.Implementations.Blockchains.LevelDB.DebugStorage import DebugStorage

from neo.Core.State.AccountState import AccountState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem

from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.Core.TX.Transaction import TransactionOutput

from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType
from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.SmartContract.Contract import Contract
from neocore.Cryptography.Helper import scripthash_to_address
from neocore.Cryptography.Crypto import Crypto
from neocore.Fixed8 import Fixed8
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neo.EventHub import events
from logzero import logger
from prompt_toolkit import prompt

from neocore.Cryptography.ECCurve import ECDSA

from neo.VM.OpCode import PACK

DEFAULT_MIN_FEE = Fixed8.FromDecimal(.0001)


def InvokeContract(wallet, tx, fee=Fixed8.Zero(), from_addr=None, owners=None):

    if from_addr is not None:
        from_addr = lookup_addr_str(wallet, from_addr)

    wallet_tx = wallet.MakeTransaction(tx=tx, fee=fee, use_standard=True, from_addr=from_addr)

    if wallet_tx:

        context = ContractParametersContext(wallet_tx)
        wallet.Sign(context)

        if owners:
            gather_signatures(context, wallet_tx, list(owners))

        if context.Completed:

            wallet_tx.scripts = context.GetScripts()

            relayed = False

#            print("SENDING TX: %s " % json.dumps(wallet_tx.ToJson(), indent=4))

            relayed = NodeLeader.Instance().Relay(wallet_tx)

            if relayed:
                print("Relayed Tx: %s " % wallet_tx.Hash.ToString())

                wallet.SaveTransaction(wallet_tx)

                return wallet_tx
            else:
                print("Could not relay tx %s " % wallet_tx.Hash.ToString())
        else:

            print("Incomplete signature")

    else:
        print("Insufficient funds")

    return False


def InvokeWithTokenVerificationScript(wallet, tx, token, fee=Fixed8.Zero(), invoke_attrs=None):

    wallet_tx = wallet.MakeTransaction(tx=tx, fee=fee, use_standard=True)

    if wallet_tx:

        token_contract_state = Blockchain.Default().GetContract(token.ScriptHash.ToString())
        print("token contract  %s " % token_contract_state)

        tx.Attributes = [
            TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                 data=token.ScriptHash.Data)
        ]

        if invoke_attrs:
            tx.Attributes += invoke_attrs

        reedeem_script = token_contract_state.Code.Script.hex()

        # there has to be at least 1 param, and the first
        # one needs to be a signature param
        param_list = bytearray(b'\x00\x00')

        verification_contract = Contract.Create(reedeem_script, param_list, wallet.GetDefaultContract().PublicKeyHash)

        context = ContractParametersContext(wallet_tx)

        wallet.Sign(context)

        context.Add(verification_contract, 0, 0)

        if context.Completed:

            wallet_tx.scripts = context.GetScripts()

            relayed = NodeLeader.Instance().Relay(wallet_tx)

            if relayed:
                print("Relayed Tx: %s " % wallet_tx.Hash.ToString())

                # if it was relayed, we save tx
                wallet.SaveTransaction(wallet_tx)

                return wallet_tx
            else:
                print("Could not relay tx %s " % wallet_tx.Hash.ToString())
        else:

            print("Incomplete signature")

    else:
        print("Insufficient funds")

    return False


def TestInvokeContract(wallet, args, withdrawal_tx=None,
                       parse_params=True, from_addr=None,
                       min_fee=DEFAULT_MIN_FEE, invoke_attrs=None, owners=None):

    BC = GetBlockchain()

    contract = BC.GetContract(args[0])

    if contract:
        #
        params = args[1:] if len(args) > 1 else []

        params, neo_to_attach, gas_to_attach = get_asset_attachments(params)
        params.reverse()

        sb = ScriptBuilder()

        for p in params:

            if parse_params:
                item = parse_param(p, wallet)
            else:
                item = p
            if type(item) is list:
                item.reverse()
                listlength = len(item)
                for listitem in item:
                    subitem = parse_param(listitem, wallet)
                    if type(subitem) is list:
                        subitem.reverse()
                        for listitem2 in subitem:
                            subsub = parse_param(listitem2, wallet)
                            sb.push(subsub)
                        sb.push(len(subitem))
                        sb.Emit(PACK)
                    else:
                        sb.push(subitem)

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

        return test_invoke(out, wallet, outputs, withdrawal_tx, from_addr, min_fee, invoke_attrs=invoke_attrs, owners=owners)

    else:

        print("Contract %s not found" % args[0])

    return None, None, None, None


def test_invoke(script, wallet, outputs, withdrawal_tx=None,
                from_addr=None, min_fee=DEFAULT_MIN_FEE,
                invoke_attrs=None, owners=None):

    # print("invoke script %s " % script)

    if from_addr is not None:
        from_addr = lookup_addr_str(wallet, from_addr)

    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    # if we are using a withdrawal tx, don't recreate the invocation tx
    # also, we don't want to reset the inputs / outputs
    # since those were already calculated
    if withdrawal_tx is not None:
        tx = withdrawal_tx

    else:
        tx = InvocationTransaction()
        tx.outputs = outputs
        tx.inputs = []

    tx.Version = 1
    tx.scripts = []
    tx.Script = binascii.unhexlify(script)
    tx.Attributes = [] if invoke_attrs is None else invoke_attrs

    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

    if len(outputs) < 1:
        contract = wallet.GetDefaultContract()
        tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=contract.ScriptHash))

    # same as above. we don't want to re-make the transaction if it is a withdrawal tx
    if withdrawal_tx is not None:
        wallet_tx = tx
    else:
        wallet_tx = wallet.MakeTransaction(tx=tx, from_addr=from_addr)

    context = ContractParametersContext(wallet_tx)
    wallet.Sign(context)

    if owners:
        owners = list(owners)
        for owner in owners:
            #            print("contract %s %s" % (wallet.GetDefaultContract().ScriptHash, owner))
            if wallet.GetDefaultContract().ScriptHash != owner:
                wallet_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))
        context = ContractParametersContext(wallet_tx, isMultiSig=True)

    if context.Completed:
        wallet_tx.scripts = context.GetScripts()
    else:
        logger.warn("Not gathering signatures for test build.  For a non-test invoke that would occur here.")
#        if not gather_signatures(context, wallet_tx, owners):
#            return None, [], 0, None

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
        success = engine.Execute()

        service.ExecutionCompleted(engine, success)

        for event in service.events_to_dispatch:
            events.emit(event.event_type, event)

        if success:

            # this will be removed in favor of neo.EventHub
            if len(service.notifications) > 0:
                for n in service.notifications:
                    Blockchain.Default().OnNotify(n)

            print("Used %s Gas " % engine.GasConsumed().ToString())

            consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
            consumed = consumed.Ceil()

            net_fee = None
            tx_gas = None

            if consumed <= Fixed8.Zero():
                net_fee = min_fee
                tx_gas = Fixed8.Zero()
            else:
                tx_gas = consumed
                net_fee = Fixed8.Zero()

            # set the amount of gas the tx will need
            wallet_tx.Gas = tx_gas
            # reset the wallet outputs
            wallet_tx.outputs = outputs
            wallet_tx.Attributes = []

            return wallet_tx, net_fee, engine.EvaluationStack.Items, engine.ops_processed

        # this allows you to to test invocations that fail
        else:
            wallet_tx.outputs = outputs
            wallet_tx.Attributes = []
            return wallet_tx, min_fee, [], engine.ops_processed

    except Exception as e:
        service.ExecutionCompleted(engine, False, e)
#        print("COULD NOT EXECUTE %s " % e)

    return None, None, None, None


def test_deploy_and_invoke(deploy_script, invoke_args, wallet,
                           from_addr=None, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True,
                           debug_map=None, invoke_attrs=None, owners=None):

    bc = GetBlockchain()

    sn = bc._db.snapshot()

    accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
    assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
    validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
    storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

    if settings.USE_DEBUG_STORAGE:
        debug_storage = DebugStorage.instance()
        debug_sn = debug_storage.db.snapshot()
        storages = DBCollection(debug_storage.db, debug_sn, DBPrefix.ST_Storage, StorageItem)
        storages.DebugStorage = True

    dtx = InvocationTransaction()
    dtx.Version = 1
    dtx.outputs = []
    dtx.inputs = []
    dtx.scripts = []
    dtx.Script = binascii.unhexlify(deploy_script)

    if from_addr is not None:
        from_addr = lookup_addr_str(wallet, from_addr)

    dtx = wallet.MakeTransaction(tx=dtx, from_addr=from_addr)
    context = ContractParametersContext(dtx)
    wallet.Sign(context)
    dtx.scripts = context.GetScripts()

    script_table = CachedScriptTable(contracts)
    service = StateMachine(accounts, validators, assets, contracts, storages, None)

    contract = wallet.GetDefaultContract()
    dtx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash(contract.Script, unhex=False))]

    to_dispatch = []

    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=dtx,
        table=script_table,
        service=service,
        gas=dtx.Gas,
        testMode=True
    )

    engine.LoadScript(dtx.Script, False)

    # first we will execute the test deploy
    # then right after, we execute the test invoke

    d_success = engine.Execute()

    if d_success:

        items = engine.EvaluationStack.Items

        contract_state = None
        for i in items:
            if type(i) is ContractState:
                contract_state = i
                break
            elif type(i) is InteropInterface:
                item = i.GetInterface()
                if type(item) is ContractState:
                    contract_state = item
                    break

        shash = contract_state.Code.ScriptHash()

        invoke_args, neo_to_attach, gas_to_attach = get_asset_attachments(invoke_args)
        invoke_args.reverse()

        sb = ScriptBuilder()

        for p in invoke_args:
            item = parse_param(p, wallet)
            if type(item) is list:
                item.reverse()
                listlength = len(item)
                for listitem in item:
                    subitem = parse_param(listitem, wallet)
                    if type(subitem) is list:
                        subitem.reverse()
                        for listitem2 in subitem:
                            subsub = parse_param(listitem2, wallet)
                            sb.push(subsub)
                        sb.push(len(subitem))
                        sb.Emit(PACK)
                    else:
                        sb.push(subitem)

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
        itx.Attributes = invoke_attrs if invoke_attrs else []
        itx.Script = binascii.unhexlify(out)

        if len(outputs) < 1 and not owners:
            contract = wallet.GetDefaultContract()
            itx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                       data=contract.ScriptHash))

        itx = wallet.MakeTransaction(tx=itx, from_addr=from_addr)

        context = ContractParametersContext(itx)
        wallet.Sign(context)

        if owners:
            owners = list(owners)
            for owner in owners:
                itx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))
            context = ContractParametersContext(itx, isMultiSig=True)

        if context.Completed:
            itx.scripts = context.GetScripts()
        else:
            logger.warn("Not gathering signatures for test build.  For a non-test invoke that would occur here.")
#            if not gather_signatures(context, itx, owners):
#                return None, [], 0, None

#        print("gathered signatures %s " % itx.scripts)

        engine = ApplicationEngine(
            trigger_type=TriggerType.Application,
            container=itx,
            table=script_table,
            service=service,
            gas=itx.Gas,
            testMode=invocation_test_mode
        )

        engine.LoadScript(itx.Script, False)
        engine.LoadDebugInfoForScriptHash(debug_map, shash.Data)

        # call execute in its own blocking thread

#        reactor.stop()

        i_success = engine.Execute()

        service.ExecutionCompleted(engine, i_success)
        to_dispatch = to_dispatch + service.events_to_dispatch

        for event in to_dispatch:
            events.emit(event.event_type, event)

        if i_success:
            service.TestCommit()
            if len(service.notifications) > 0:

                for n in service.notifications:
                    Blockchain.Default().OnNotify(n)

            logger.info("Used %s Gas " % engine.GasConsumed().ToString())

            consumed = engine.GasConsumed() - Fixed8.FromDecimal(10)
            consumed = consumed.Ceil()

            if consumed <= Fixed8.Zero():
                consumed = min_fee

            total_ops = engine.ops_processed

            # set the amount of gas the tx will need
            itx.Gas = consumed
            itx.Attributes = []
            result = engine.EvaluationStack.Items
            return itx, result, total_ops, engine
        else:
            print("error executing invoke contract...")

    else:
        print("error executing deploy contract.....")

    service.ExecutionCompleted(engine, False, 'error')

    return None, [], 0, None


def gather_signatures(context, itx, owners):
    do_exit = False
    print("owners %s " % owners)
    print("\n\n*******************\n")
    print("Gather Signatures for Transactino:\n%s " % json.dumps(itx.ToJson(), indent=4))
    print("Please use a client to sign the following: %s " % itx.GetHashData())

    owner_index = 0
    while not context.Completed and not do_exit:

        next_script = owners[owner_index]
        next_addr = scripthash_to_address(next_script.Data)
        try:
            print("\n*******************\n")
            owner_input = prompt('Public Key and Signature for %s> ' % next_addr)
            items = owner_input.split(' ')
            pubkey = ECDSA.decode_secp256r1(items[0]).G
            sig = items[1]
            contract = Contract.CreateSignatureContract(pubkey)

            if contract.Address == next_addr:
                context.Add(contract, 0, sig)
                print("Adding signature %s " % sig)
                owner_index += 1
            else:
                print("Public Key does not match address %s " % next_addr)

        except EOFError:
            # Control-D pressed: quit
            do_exit = True
        except KeyboardInterrupt:
            # Control-C pressed: do nothing
            do_exit = True
        except Exception as e:
            print("Could not parse input %s " % e)

    if context.Completed:
        print("Signatures complete")
        itx.scripts = context.GetScripts()
        return True
    else:
        print("Could not finish signatures")
        return False
