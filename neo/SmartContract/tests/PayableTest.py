from boa.interop.Neo.Blockchain import GetContract
from boa.interop.Neo.Contract import Contract
from boa.interop.System.ExecutionEngine import GetExecutingScriptHash


def Main(operation):

    if operation == 'payable':
        script_hash = GetExecutingScriptHash()
        contract = GetContract(script_hash)
        return contract.IsPayable

    return 'unknown operation'
