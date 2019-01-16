import binascii
from neo.Prompt.Utils import parse_param
from neo.Core.FunctionCode import FunctionCode
from neo.Core.State.ContractState import ContractPropertyState
from neo.SmartContract.ContractParameterType import ContractParameterType
from prompt_toolkit import prompt
import json
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Core.Blockchain import Blockchain
from neo.SmartContract.Contract import Contract
from neocore.BigInteger import BigInteger
from neo.Prompt.PromptPrinter import prompt_print as print


def ImportContractAddr(wallet, contract_hash, pubkey_script_hash):
    """
    Args:
        wallet (Wallet): a UserWallet instance
        contract_hash (UInt160): hash of the contract to import
        pubkey_script_hash (UInt160):

    Returns:
        neo.SmartContract.Contract.Contract
    """

    contract = Blockchain.Default().GetContract(contract_hash)
    if not contract or not pubkey_script_hash:
        print("Could not find contract")
        return

    reedeem_script = contract.Code.Script.hex()

    # there has to be at least 1 param, and the first one needs to be a signature param
    param_list = bytearray(b'\x00')

    # if there's more than one param
    # we set the first parameter to be the signature param
    if len(contract.Code.ParameterList) > 1:
        param_list = bytearray(contract.Code.ParameterList)
        param_list[0] = 0

    verification_contract = Contract.Create(reedeem_script, param_list, pubkey_script_hash)

    address = verification_contract.Address

    wallet.AddContract(verification_contract)

    print(f"Added contract address {address} to wallet")
    return verification_contract


def LoadContract(path, needs_storage, needs_dynamic_invoke, is_payable, params_str, return_type):
    params = parse_param(params_str, ignore_int=True, prefer_hex=False)

    if type(params) is str:
        params = params.encode('utf-8')

    try:
        for p in binascii.unhexlify(params):
            if p == ContractParameterType.Void.value:
                raise ValueError("Void is not a valid input parameter type")
    except binascii.Error:
        pass

    rtype = BigInteger(ContractParameterType.FromString(return_type).value)

    contract_properties = 0

    if needs_storage:
        contract_properties += ContractPropertyState.HasStorage

    if needs_dynamic_invoke:
        contract_properties += ContractPropertyState.HasDynamicInvoke

    if is_payable:
        contract_properties += ContractPropertyState.Payable

    if '.avm' not in path:
        raise ValueError("Please load a compiled .avm file")

    script = None
    with open(path, 'rb') as f:

        content = f.read()

        try:
            content = binascii.unhexlify(content)
        except Exception as e:
            pass

        script = content

    if script:
        try:
            plist = bytearray(binascii.unhexlify(params))
        except Exception as e:
            plist = bytearray(b'\x10')
        function_code = FunctionCode(script=script, param_list=bytearray(plist), return_type=rtype, contract_properties=contract_properties)

        return function_code
    else:
        raise Exception(f"Error loading contract for path {path}")


def GatherLoadedContractParams(args, script):
    if len(args) < 5:
        raise Exception("please specify contract properties like {needs_storage} {needs_dynamic_invoke} {is_payable} {params} {return_type}")
    params = parse_param(args[3], ignore_int=True, prefer_hex=False)

    if type(params) is str:
        params = params.encode('utf-8')

    try:
        for p in binascii.unhexlify(params):
            if p == ContractParameterType.Void.value:
                raise ValueError("Void is not a valid input parameter type")
    except binascii.Error:
        pass

    return_type = BigInteger(ContractParameterType.FromString(args[4]).value)

    needs_storage = bool(parse_param(args[0]))
    needs_dynamic_invoke = bool(parse_param(args[1]))
    is_payable = bool(parse_param(args[2]))

    contract_properties = 0

    if needs_storage:
        contract_properties += ContractPropertyState.HasStorage

    if needs_dynamic_invoke:
        contract_properties += ContractPropertyState.HasDynamicInvoke

    if is_payable:
        contract_properties += ContractPropertyState.Payable

    out = generate_deploy_script(script, contract_properties=contract_properties, return_type=return_type, parameter_list=params)

    return out


def GatherContractDetails(function_code):
    print("Please fill out the following contract details:")

    name = prompt("[Contract Name] > ")
    version = prompt("[Contract Version] > ")
    author = prompt("[Contract Author] > ")
    email = prompt("[Contract Email] > ")
    description = prompt("[Contract Description] > ")

    print("Creating smart contract....")
    print("                 Name: %s " % name)
    print("              Version: %s" % version)
    print("               Author: %s " % author)
    print("                Email: %s " % email)
    print("          Description: %s " % description)
    print("        Needs Storage: %s " % function_code.HasStorage)
    print(" Needs Dynamic Invoke: %s " % function_code.HasDynamicInvoke)
    print("           Is Payable: %s " % function_code.IsPayable)
    print(json.dumps(function_code.ToJson(), indent=4))

    return generate_deploy_script(function_code.Script, name, version, author, email, description,
                                  function_code.ContractProperties, function_code.ReturnTypeBigInteger,
                                  function_code.ParameterList)


def generate_deploy_script(script, name='test', version='test', author='test', email='test',
                           description='test', contract_properties=0, return_type=BigInteger(255), parameter_list=[]):
    sb = ScriptBuilder()

    plist = parameter_list
    try:
        plist = bytearray(binascii.unhexlify(parameter_list))
    except Exception as e:
        pass

    sb.push(binascii.hexlify(description.encode('utf-8')))
    sb.push(binascii.hexlify(email.encode('utf-8')))
    sb.push(binascii.hexlify(author.encode('utf-8')))
    sb.push(binascii.hexlify(version.encode('utf-8')))
    sb.push(binascii.hexlify(name.encode('utf-8')))
    sb.push(contract_properties)
    sb.push(return_type)
    sb.push(plist)
    sb.WriteVarData(script)
    sb.EmitSysCall("Neo.Contract.Create")
    script = sb.ToArray()

    return script
