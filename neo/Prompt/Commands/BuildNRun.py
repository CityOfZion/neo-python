from neo.Prompt.Utils import get_arg
from neo.Prompt.Commands.LoadSmartContract import GatherLoadedContractParams
from neo.Prompt.Commands.Invoke import test_deploy_and_invoke
from neo.Fixed8 import Fixed8
from boa.compiler import Compiler

import binascii
import traceback


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


def BuildAndRun(arguments, wallet):
    path = get_arg(arguments)

    try:
        contract_script = Compiler.instance().load_and_save(path)

        newpath = path.replace('.py', '.avm')
        print("Saved output to %s " % newpath)

        DoRun(contract_script, arguments, wallet, path)

    except Exception as e:
        print("Could not compile %s " % e)


def DoRun(contract_script, arguments, wallet, path):

    try:

        test = get_arg(arguments, 1)

        if test is not None and test == 'test':

            if wallet is not None:

                f_args = arguments[2:]
                i_args = arguments[6:]

                script = GatherLoadedContractParams(f_args, contract_script)

                tx, result, total_ops = test_deploy_and_invoke(script, i_args, wallet)
                i_args.reverse()

                if tx is not None and result is not None:
                    print("\n-----------------------------------------------------------")
                    print("Calling %s with arguments %s " % (path, i_args))
                    print("Test deploy invoke successful")
                    print("Used total of %s operations " % total_ops)
                    print("Result %s " % result)
                    print("Invoke TX gas cost: %s " % (tx.Gas.value / Fixed8.D))
                    print("-------------------------------------------------------------\n")

                    return
                else:
                    print("Test invoke failed")
                    print("tx is, results are %s %s " % (tx, result))
                    return

            else:

                print("please open a wallet to test built contract")

    except Exception as e:
        print("could not bulid %s " % e)
        traceback.print_stack()
        traceback.print_exc()
