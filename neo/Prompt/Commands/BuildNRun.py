from neo.Prompt.Utils import get_arg
from neo.Prompt.Commands.LoadSmartContract import GatherLoadedContractParams
from neo.Prompt.Commands.Invoke import test_deploy_and_invoke
from neo.Fixed8 import Fixed8
from boa.boa import Compiler



def BuildAndRun(arguments, wallet):
    path = get_arg(arguments)

    try:
        contract_script = Compiler.Instance().LoadAndSave(path)
        newpath = path.replace('.py' ,'.avm')
        print("Saved output to %s " % newpath)

        test = get_arg(arguments, 1)

        if test is not None and test == 'test':

            if wallet is not None:

                f_args = arguments[2:]
                i_args = arguments[5:]

                script = GatherLoadedContractParams(f_args, contract_script)

                tx ,results = test_deploy_and_invoke(script, i_args, wallet)

                if tx is not None and results is not None:
                    print("\n-----------------------------------------------------------")
                    print("Calling %s with arguments %s " % (path, i_args))
                    print("Test deploy invoke successful")
                    print("Results %s " % [str(item) for item in results])
                    print("Invoke TX gas cost: %s " % (int(tx.Gas.value / Fixed8.D)))
                    print("-------------------------------------------------------------\n")
                    return
                else:
                    print("test ivoke failed")
                    print("tx is, results are %s %s " % (tx, results))
                    return



            else:

                print("please open a wallet to test built contract")



    except Exception as e:
        print("could not bulid %s " % e)