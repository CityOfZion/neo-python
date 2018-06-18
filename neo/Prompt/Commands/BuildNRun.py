from neo.Prompt.Utils import get_arg, get_from_addr, get_tx_attr_from_args, get_owners_from_params
from neo.Prompt.Commands.LoadSmartContract import GatherLoadedContractParams, generate_deploy_script
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.SmartContract.ContractParameter import ContractParameter
from neo.Prompt.Commands.Invoke import test_deploy_and_invoke, DEFAULT_MIN_FEE
from neocore.Fixed8 import Fixed8
from boa.compiler import Compiler
from logzero import logger
import binascii
from neo.Core.State.ContractState import ContractPropertyState
import os
import json
from neocore.BigInteger import BigInteger


def LoadAndRun(arguments, wallet):

    arguments, from_addr = get_from_addr(arguments)

    path = get_arg(arguments)

    try:

        with open(path, 'rb') as f:

            content = f.read()

            try:
                content = binascii.unhexlify(content)
            except Exception as e:
                pass

            script = content

            print("arguments.... %s " % arguments)
            DoRun(script, arguments, wallet, path, from_addr=from_addr)

    except Exception as e:
        print("Could not load script %s " % e)


def BuildAndRun(arguments, wallet, verbose=True, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True):

    arguments, from_addr = get_from_addr(arguments)
    arguments, invoke_attrs = get_tx_attr_from_args(arguments)
    arguments, owners = get_owners_from_params(arguments)
    path = get_arg(arguments)
    contract_script = Compiler.instance().load_and_save(path)

    newpath = path.replace('.py', '.avm')
    logger.info("Saved output to %s " % newpath)

    debug_map_path = path.replace('.py', '.debug.json')
    debug_map = None
    if os.path.exists(debug_map_path):
        with open(debug_map_path, 'r') as dbg:
            debug_map = json.load(dbg)

    return DoRun(contract_script, arguments, wallet, path, verbose,
                 from_addr, min_fee, invocation_test_mode,
                 debug_map=debug_map, invoke_attrs=invoke_attrs, owners=owners)


def DoRun(contract_script, arguments, wallet, path, verbose=True,
          from_addr=None, min_fee=DEFAULT_MIN_FEE, invocation_test_mode=True,
          debug_map=None, invoke_attrs=None, owners=None):

    test = get_arg(arguments, 1)

    if test is not None and test == 'test':

        if wallet is not None:

            f_args = arguments[2:]
            i_args = arguments[6:]

            script = GatherLoadedContractParams(f_args, contract_script)

            tx, result, total_ops, engine = test_deploy_and_invoke(script, i_args, wallet, from_addr,
                                                                   min_fee, invocation_test_mode, debug_map=debug_map,
                                                                   invoke_attrs=invoke_attrs, owners=owners)
            i_args.reverse()

            return_type_results = []

            try:
                rtype = ContractParameterType.FromString(f_args[1])
                for r in result:
                    cp = ContractParameter.AsParameterType(rtype, r)
                    return_type_results.append(cp.ToJson())
            except Exception as e:
                logger.error('Could not convert result to ContractParameter: %s ' % e)

            if tx is not None and result is not None:
                if verbose:
                    print("\n-----------------------------------------------------------")
                    print("Calling %s with arguments %s " % (path, i_args))
                    print("Test deploy invoke successful")
                    print("Used total of %s operations " % total_ops)
                    print("Result %s " % return_type_results)
                    print("Invoke TX gas cost: %s " % (tx.Gas.value / Fixed8.D))
                    print("-------------------------------------------------------------\n")

                return tx, result, total_ops, engine
            else:
                if verbose:
                    print("Test invoke failed")
                    print("tx is, results are %s %s " % (tx, result))

        else:

            print("please open a wallet to test built contract")

    return None, None, None, None


def TestBuild(script, invoke_args, wallet, plist='05', ret='05', dynamic=False, invoke_attrs=None, owners=None):

    properties = ContractPropertyState.HasStorage

    if dynamic:
        properties += ContractPropertyState.HasDynamicInvoke

    if not isinstance(ret, bytearray):
        ret = bytearray(binascii.unhexlify(str(ret).encode('utf-8')))

    script = generate_deploy_script(script, contract_properties=int(properties), parameter_list=plist, return_type=BigInteger.FromBytes(ret))

    return test_deploy_and_invoke(script, invoke_args, wallet, invoke_attrs=invoke_attrs, owners=owners)
