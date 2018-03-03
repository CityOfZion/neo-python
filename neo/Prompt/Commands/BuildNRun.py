from neo.Prompt.Utils import get_arg
from neo.Prompt.Commands.LoadSmartContract import GatherLoadedContractParams, generate_deploy_script
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.SmartContract.ContractParameter import ContractParameter
from neo.Prompt.Commands.Invoke import test_deploy_and_invoke, DEFAULT_MIN_FEE
from neocore.Fixed8 import Fixed8
from boa.compiler import Compiler
from logzero import logger
import binascii
import traceback
from neo.Core.State.ContractState import ContractPropertyState


def LoadAndRun(arguments, wallet):

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
            DoRun(script, arguments, wallet, path)

    except Exception as e:
        print("Could not load script %s " % e)


def BuildAndRun(arguments, wallet, verbose=True, min_fee=DEFAULT_MIN_FEE):
    path = get_arg(arguments)

    contract_script = Compiler.instance().load_and_save(path)

    newpath = path.replace('.py', '.avm')
    print("Saved output to %s " % newpath)

    return DoRun(contract_script, arguments, wallet, path, verbose, min_fee=min_fee)


def DoRun(contract_script, arguments, wallet, path, verbose=True, min_fee=DEFAULT_MIN_FEE):

    test = get_arg(arguments, 1)

    if test is not None and test == 'test':

        if wallet is not None:

            f_args = arguments[2:]
            i_args = arguments[6:]

            script = GatherLoadedContractParams(f_args, contract_script)

            tx, result, total_ops, engine = test_deploy_and_invoke(script, i_args, wallet, min_fee)
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


def TestBuild(script, invoke_args, wallet, plist='05', ret='05', dynamic=False):

    properties = ContractPropertyState.HasStorage

    if dynamic:
        properties += ContractPropertyState.HasDynamicInvoke

    script = generate_deploy_script(script, contract_properties=int(properties), parameter_list=plist, return_type=ret)

    return test_deploy_and_invoke(script, invoke_args, wallet)
