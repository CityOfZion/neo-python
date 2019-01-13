from neo.Prompt.Utils import get_arg, get_from_addr, get_tx_attr_from_args, get_owners_from_params
from neo.Prompt.Commands.LoadSmartContract import GatherLoadedContractParams, generate_deploy_script
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.SmartContract.ContractParameter import ContractParameter
from neo.Prompt.Commands.Invoke import test_deploy_and_invoke, DEFAULT_MIN_FEE
from neocore.Fixed8 import Fixed8
from boa.compiler import Compiler
import binascii
from neo.Core.State.ContractState import ContractPropertyState
import os
import json
import traceback
from neocore.BigInteger import BigInteger
from neo.Settings import settings
from neo.logging import log_manager
from neo.Prompt.PromptPrinter import prompt_print as print

logger = log_manager.getLogger()


def LoadAndRun(arguments, wallet):
    arguments, from_addr = get_from_addr(arguments)

    path = get_arg(arguments)

    if '.avm' not in path:
        raise TypeError

    with open(path, 'rb') as f:

        content = f.read()

        try:
            content = binascii.unhexlify(content)
        except Exception:
            pass

        script = content

        return DoRun(script, arguments, wallet, path, from_addr=from_addr)


def Build(arguments):
    path = get_arg(arguments)
    try:
        contract_script = Compiler.instance().load_and_save(path, use_nep8=settings.COMPILER_NEP_8)
    except FileNotFoundError:
        return

    newpath = path.replace('.py', '.avm')
    print("Saved output to %s " % newpath)
    return contract_script


def BuildAndRun(arguments, wallet, verbose=True, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True):
    arguments, from_addr = get_from_addr(arguments)
    arguments, invoke_attrs = get_tx_attr_from_args(arguments)
    arguments, owners = get_owners_from_params(arguments)
    path = get_arg(arguments)

    contract_script = Build(arguments)

    if contract_script is not None:
        debug_map_path = path.replace('.py', '.debug.json')
        debug_map = None
        if os.path.exists(debug_map_path):
            with open(debug_map_path, 'r') as dbg:
                debug_map = json.load(dbg)

        return DoRun(contract_script, arguments, wallet, path, verbose,
                     from_addr, min_fee, invocation_test_mode,
                     debug_map=debug_map, invoke_attrs=invoke_attrs, owners=owners)
    else:
        print('Please check the path to your Python (.py) file to compile')
        return None, None, None, None


def DoRun(contract_script, arguments, wallet, path, verbose=True,
          from_addr=None, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True,
          debug_map=None, invoke_attrs=None, owners=None):
    if not wallet:
        print("Please open a wallet to test build contract")
        return None, None, None, None

    f_args = arguments[1:]
    i_args = arguments[6:]

    try:
        script = GatherLoadedContractParams(f_args, contract_script)
    except Exception:
        raise TypeError

    tx, result, total_ops, engine = test_deploy_and_invoke(script, i_args, wallet, from_addr,
                                                           min_fee, invocation_test_mode, debug_map=debug_map,
                                                           invoke_attrs=invoke_attrs, owners=owners)
    i_args.reverse()

    return_type_results = []
    try:
        rtype = ContractParameterType.FromString(f_args[4])
        for r in result:
            cp = ContractParameter.AsParameterType(rtype, r)
            return_type_results.append(cp.ToJson())
    except Exception:
        raise TypeError

    if tx and result:
        if verbose:
            print("\n-----------------------------------------------------------")
            print("Calling %s with arguments %s " % (path, [item for item in reversed(engine.invocation_args)]))
            print("Test deploy invoke successful")
            print("Used total of %s operations " % total_ops)
            print("Result %s " % return_type_results)
            print("Invoke TX gas cost: %s " % (tx.Gas.value / Fixed8.D))
            print("-------------------------------------------------------------\n")

        return tx, result, total_ops, engine
    else:
        if verbose:
            print("Test invoke failed")
            print(f"tx is {tx}, results are {result}")
        return tx, result, None, None


def TestBuild(script, invoke_args, wallet, plist='05', ret='05', dynamic=False, invoke_attrs=None, owners=None):
    properties = ContractPropertyState.HasStorage

    if dynamic:
        properties += ContractPropertyState.HasDynamicInvoke

    if not isinstance(ret, bytearray):
        ret = bytearray(binascii.unhexlify(str(ret).encode('utf-8')))

    script = generate_deploy_script(script, contract_properties=int(properties), parameter_list=plist, return_type=BigInteger.FromBytes(ret))

    return test_deploy_and_invoke(script, invoke_args, wallet, invoke_attrs=invoke_attrs, owners=owners)
