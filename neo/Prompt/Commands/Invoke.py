import binascii
import json
from neo.Blockchain import GetBlockchain
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.InteropService import InteropInterface
from neo.Prompt import Utils as PromptUtils
from neo.Storage.Interface.DBInterface import DBInterface
from neo.Storage.Common.CachedScriptTable import CachedScriptTable
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Storage.Common.DebugStorage import DebugStorage


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
from neo.Core.Cryptography.Helper import scripthash_to_address
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Fixed8 import Fixed8
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neo.EventHub import events
from neo.Network.common import blocking_prompt as prompt
from copy import deepcopy
from neo.logging import log_manager
from neo.Prompt.PromptPrinter import prompt_print as print
from neo.Network.nodemanager import NodeManager
from neo.Core.Utils import validate_simple_policy

logger = log_manager.getLogger()

from neo.Core.Cryptography.ECCurve import ECDSA
from neo.Core.UInt160 import UInt160
from neo.VM.OpCode import PACK
from neo.VM.Debugger import Debugger

DEFAULT_MIN_FEE = Fixed8.FromDecimal(.0001)


def InvokeContract(wallet, tx, fee=Fixed8.Zero(), from_addr=None, owners=None):
    if from_addr is not None:
        from_addr = PromptUtils.lookup_addr_str(wallet, from_addr)

    try:
        wallet_tx = wallet.MakeTransaction(tx=tx, fee=fee, use_standard=True, from_addr=from_addr)
    except ValueError:
        print("Insufficient funds")
        return False

    if wallet_tx:

        if owners:
            for owner in list(owners):
                wallet_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))
            wallet_tx.Attributes = make_unique_script_attr(tx.Attributes)

        context = ContractParametersContext(wallet_tx)
        wallet.Sign(context)

        if owners:
            gather_signatures(context, wallet_tx, list(owners))

        if context.Completed:

            wallet_tx.scripts = context.GetScripts()

            passed, reason = validate_simple_policy(wallet_tx)
            if not passed:
                print(reason)
                return False

            nodemgr = NodeManager()
            relayed = nodemgr.relay(wallet_tx)

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
    try:
        wallet_tx = wallet.MakeTransaction(tx=tx, fee=fee, use_standard=True)
    except ValueError:
        print("Insufficient funds")
        return False

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

            nodemgr = NodeManager()
            relayed = nodemgr.relay(wallet_tx)

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


def TestInvokeContract(wallet, args, withdrawal_tx=None, from_addr=None,
                       min_fee=DEFAULT_MIN_FEE, invoke_attrs=None, owners=None):
    BC = GetBlockchain()

    contract = BC.GetContract(args[0])

    if contract:
        #
        params = args[1:] if len(args) > 1 else []

        params, neo_to_attach, gas_to_attach = PromptUtils.get_asset_attachments(params)
        params, parse_addresses = PromptUtils.get_parse_addresses(params)
        params.reverse()

        if '--i' in params:
            params = []
            for index, iarg in enumerate(contract.Code.ParameterList):
                param, abort = PromptUtils.gather_param(index, iarg)
                if abort:
                    return None, None, None, None, False
                params.append(param)
            params.reverse()

        sb = ScriptBuilder()

        for p in params:
            process_params(sb, p, wallet, parse_addresses)

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

    return None, None, None, None, False


def make_unique_script_attr(attributes):
    """
    Filter out duplicate `Script` TransactionAttributeUsage types.
    Args:
        attributes: a list of TransactionAttribute's

    Returns:
        list:
    """
    filtered_attr = []
    script_list = []
    for attr in attributes:
        if attr.Usage != TransactionAttributeUsage.Script:
            filtered_attr.append(attr)
        else:
            data = attr.Data
            if isinstance(data, UInt160):
                # convert it to equal type
                data = attr.Data.ToArray()

            # only add if it's not already in the list
            if data not in script_list:
                script_list.append(data)
                filtered_attr.append(attr)

    return filtered_attr


def test_invoke(script, wallet, outputs, withdrawal_tx=None,
                from_addr=None, min_fee=DEFAULT_MIN_FEE,
                invoke_attrs=None, owners=None):
    # print("invoke script %s " % script)

    if from_addr is not None:
        from_addr = PromptUtils.lookup_addr_str(wallet, from_addr)

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
    tx.Attributes = [] if invoke_attrs is None else deepcopy(invoke_attrs)

    if len(outputs) < 1:
        contract = wallet.GetDefaultContract()
        tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=contract.ScriptHash))
        tx.Attributes = make_unique_script_attr(tx.Attributes)

    # same as above. we don't want to re-make the transaction if it is a withdrawal tx
    if withdrawal_tx is not None:
        wallet_tx = tx
    else:
        try:
            wallet_tx = wallet.MakeTransaction(tx=tx, from_addr=from_addr)
        except ValueError:
            pass

    context = ContractParametersContext(wallet_tx)
    wallet.Sign(context)

    if owners:
        owners = list(owners)
        for owner in owners:
            #            print("contract %s %s" % (wallet.GetDefaultContract().ScriptHash, owner))
            if wallet.GetDefaultContract().ScriptHash != owner:
                wallet_tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))
                wallet_tx.Attributes = make_unique_script_attr(tx.Attributes)
        context = ContractParametersContext(wallet_tx, isMultiSig=True)

    if context.Completed:
        wallet_tx.scripts = context.GetScripts()
    else:
        logger.warning("Not gathering signatures for test build.  For a non-test invoke that would occur here.")

    snapshot = GetBlockchain()._db.createSnapshot().Clone()
    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=wallet_tx,
        snapshot=snapshot,
        gas=wallet_tx.Gas,
        testMode=True
    )

    engine.LoadScript(wallet_tx.Script)

    try:
        success = engine.Execute()
        engine._Service.ExecutionCompleted(engine, success)

        for event in engine._Service.events_to_dispatch:
            events.emit(event.event_type, event)

        if success:

            # this will be removed in favor of neo.EventHub
            if len(engine._Service.notifications) > 0:
                for n in engine._Service.notifications:
                    Blockchain.Default().OnNotify(n)

            # print("Used %s Gas " % engine.GasConsumed().ToString())

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
            wallet_tx.Attributes = [] if invoke_attrs is None else deepcopy(invoke_attrs)

            return wallet_tx, net_fee, engine.ResultStack.Items, engine.ops_processed, success

        # this allows you to to test invocations that fail
        else:
            wallet_tx.outputs = outputs
            wallet_tx.Attributes = [] if invoke_attrs is None else deepcopy(invoke_attrs)
            return wallet_tx, min_fee, [], engine.ops_processed, success

    except Exception as e:
        engine._Service.ExecutionCompleted(engine, False, e)

    return None, None, None, None, False


def test_deploy_and_invoke(deploy_script, invoke_args, wallet,
                           from_addr=None, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True,
                           debug_map=None, invoke_attrs=None, owners=None, enable_debugger=False, snapshot=None):

    if settings.USE_DEBUG_STORAGE:
        debug_storage = DebugStorage.instance()
        storages = DBInterface(debug_storage.db, DBPrefix.ST_Storage, StorageItem)
        storages.DebugStorage = True

    dtx = InvocationTransaction()
    dtx.Version = 1
    dtx.outputs = []
    dtx.inputs = []
    dtx.scripts = []
    dtx.Script = binascii.unhexlify(deploy_script)

    if from_addr is not None:
        from_addr = PromptUtils.lookup_addr_str(wallet, from_addr)

    try:
        dtx = wallet.MakeTransaction(tx=dtx, from_addr=from_addr)
    except (ValueError):
        pass

    context = ContractParametersContext(dtx)
    wallet.Sign(context)
    dtx.scripts = context.GetScripts()

    contract = wallet.GetDefaultContract()
    dtx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script, data=Crypto.ToScriptHash(contract.Script, unhex=False))]
    dtx.Attributes = make_unique_script_attr(dtx.Attributes)

    to_dispatch = []

    if snapshot is None:
        snapshot = GetBlockchain()._db.createSnapshot().Clone()
    engine = ApplicationEngine(
        trigger_type=TriggerType.Application,
        container=dtx,
        snapshot=snapshot,
        gas=dtx.Gas,
        testMode=True
    )

    engine.LoadScript(dtx.Script)

    # first we will execute the test deploy
    # then right after, we execute the test invoke
    if enable_debugger:
        debugger = Debugger(engine)
        d_success = debugger.Execute()
    else:
        d_success = engine.Execute()

    # the old setup provided the same StateMachine object to the ApplicationEngine for deploy and invoke
    # this allowed for a single dispatch of events at the end of the function. Now a new StateMachine is automatically
    # created when creating an ApplicationEngine, thus we have to dispatch events after the deploy to not lose them as
    # testcases expect them
    to_dispatch = to_dispatch + engine._Service.events_to_dispatch
    for event in to_dispatch:
        events.emit(event.event_type, event)
    to_dispatch = []

    if d_success:

        items = engine.ResultStack.Items

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

        invoke_args, neo_to_attach, gas_to_attach = PromptUtils.get_asset_attachments(invoke_args)
        invoke_args, no_parse_addresses = PromptUtils.get_parse_addresses(invoke_args)

        invoke_args.reverse()

        if '--i' in invoke_args:
            invoke_args = []
            for index, iarg in enumerate(contract_state.Code.ParameterList):
                param, abort = PromptUtils.gather_param(index, iarg)
                if abort:
                    return None, [], 0, None
                else:
                    invoke_args.append(param)
            invoke_args.reverse()

        sb = ScriptBuilder()

        for p in invoke_args:
            process_params(sb, p, wallet, no_parse_addresses)

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
        itx.Attributes = deepcopy(invoke_attrs) if invoke_attrs else []
        itx.Script = binascii.unhexlify(out)

        if len(outputs) < 1 and not owners:
            contract = wallet.GetDefaultContract()
            itx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                       data=contract.ScriptHash))
            itx.Attributes = make_unique_script_attr(itx.Attributes)

        try:
            itx = wallet.MakeTransaction(tx=itx, from_addr=from_addr)
        except (ValueError):
            pass

        context = ContractParametersContext(itx)
        wallet.Sign(context)

        if owners:
            owners = list(owners)
            for owner in owners:
                itx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))
                itx.Attributes = make_unique_script_attr(itx.Attributes)
            context = ContractParametersContext(itx, isMultiSig=True)

        if context.Completed:
            itx.scripts = context.GetScripts()
        else:
            logger.warn("Not gathering signatures for test build.  For a non-test invoke that would occur here.")

        engine = ApplicationEngine(
            trigger_type=TriggerType.Application,
            container=itx,
            snapshot=snapshot,
            gas=itx.Gas,
            testMode=invocation_test_mode
        )

        engine.invocation_args = invoke_args
        engine.LoadScript(itx.Script)
        engine.LoadDebugInfoForScriptHash(debug_map, shash.Data)

        if enable_debugger:
            debugger = Debugger(engine)
            i_success = debugger.Execute()
        else:
            i_success = engine.Execute()

        engine._Service.ExecutionCompleted(engine, i_success)
        to_dispatch = to_dispatch + engine._Service.events_to_dispatch

        for event in to_dispatch:
            events.emit(event.event_type, event)

        if i_success:
            if len(engine._Service.notifications) > 0:

                for n in engine._Service.notifications:
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
            result = engine.ResultStack.Items
            return itx, result, total_ops, engine
        else:
            print("error executing invoke contract...")

    else:
        print("error executing deploy contract.....")

    # service.ExecutionCompleted(engine, False, 'error')

    return None, [], 0, None


def gather_signatures(context, itx, owners):
    do_exit = False
    print("\n\n*******************\n")
    print("Gather Signatures for Transaction:\n%s " % json.dumps(itx.ToJson(), indent=4))
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

        except ValueError:
            # expected from ECDSA if public key is invalid
            print(f"Invalid public key: {items[0]}")
            do_exit = True
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


def process_params(sb, param, wallet, no_parse_addresses):
    item = PromptUtils.parse_param(param, wallet, parse_addr=no_parse_addresses)
    if type(item) is list:
        item.reverse()
        listlength = len(item)
        for listitem in item:
            process_params(sb, listitem, wallet, no_parse_addresses)
        sb.push(listlength)
        sb.Emit(PACK)
    else:
        sb.push(item)
