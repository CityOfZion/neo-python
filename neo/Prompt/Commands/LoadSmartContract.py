import binascii
from neo.Prompt.Utils import parse_param
from neo.Core.FunctionCode import FunctionCode
from neo.Core.State.ContractState import ContractPropertyState
from neo.SmartContract.ContractParameterType import ContractParameterType
from prompt_toolkit.shortcuts import PromptSession
import json
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Prompt.Utils import get_arg
from neocore.Cryptography.Crypto import Crypto
from neo.Core.Blockchain import Blockchain
from neo.SmartContract.Contract import Contract
from neocore.BigInteger import BigInteger


def ImportContractAddr(wallet, args):
    if wallet is None:
        print("please open a wallet")
        return

    contract_hash = get_arg(args, 0)
    pubkey = get_arg(args, 1)

    if contract_hash and pubkey:

        if len(pubkey) != 66:
            print("invalid public key format")

        pubkey_script_hash = Crypto.ToScriptHash(pubkey, unhex=True)

        contract = Blockchain.Default().GetContract(contract_hash)

        if contract is not None:

            reedeem_script = contract.Code.Script.hex()

            # there has to be at least 1 param, and the first
            # one needs to be a signature param
            param_list = bytearray(b'\x00')

            # if there's more than one param
            # we set the first parameter to be the signature param
            if len(contract.Code.ParameterList) > 1:
                param_list = bytearray(contract.Code.ParameterList)
                param_list[0] = 0

            verification_contract = Contract.Create(reedeem_script, param_list, pubkey_script_hash)

            address = verification_contract.Address

            wallet.AddContract(verification_contract)

            print("Added contract addres %s to wallet" % address)
            return

    print("Could not add contract.  Invalid public key or contract address")


def LoadContract(args):
    if len(args) < 6:
        print("please specify contract to load like such: 'import contract {path} {params} {return_type} {needs_storage} {needs_dynamic_invoke} {is_payable}'")
        return

    path = args[0]
    params = parse_param(args[1], ignore_int=True, prefer_hex=False)

    if type(params) is str:
        params = params.encode('utf-8')

    return_type = BigInteger(ContractParameterType.FromString(args[2]).value)

    needs_storage = bool(parse_param(args[3]))
    needs_dynamic_invoke = bool(parse_param(args[4]))
    is_payable = bool(parse_param(args[5]))

    contract_properties = 0

    if needs_storage:
        contract_properties += ContractPropertyState.HasStorage

    if needs_dynamic_invoke:
        contract_properties += ContractPropertyState.HasDynamicInvoke

    if is_payable:
        contract_properties += ContractPropertyState.Payable

    script = None

    if '.py' in path:
        print("Please load a compiled .avm file")
        return False

    with open(path, 'rb') as f:

        content = f.read()

        try:
            content = binascii.unhexlify(content)
        except Exception as e:
            pass

        script = content

    if script is not None:

        plist = params

        try:
            plist = bytearray(binascii.unhexlify(params))
        except Exception as e:
            plist = bytearray(b'\x10')
        function_code = FunctionCode(script=script, param_list=bytearray(plist), return_type=return_type, contract_properties=contract_properties)

        return function_code

    print("error loading contract for path %s" % path)
    return None


def GatherLoadedContractParams(args, script):
    if len(args) < 5:
        raise Exception("please specify contract properties like {params} {return_type} {needs_storage} {needs_dynamic_invoke} {is_payable}")
    params = parse_param(args[0], ignore_int=True, prefer_hex=False)

    if type(params) is str:
        params = params.encode('utf-8')

    return_type = BigInteger(ContractParameterType.FromString(args[1]).value)

    needs_storage = bool(parse_param(args[2]))
    needs_dynamic_invoke = bool(parse_param(args[3]))
    is_payable = bool(parse_param(args[4]))

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

    from neo.bin.prompt import PromptInterface

    session = PromptSession(completer=PromptInterface.prompt_completer,
                            history=PromptInterface.history)

    name = session.prompt("[Contract Name] > ")
    version = session.prompt("[Contract Version] > ")
    author = session.prompt("[Contract Author] > ")
    email = session.prompt("[Contract Email] > ")
    description = session.prompt("[Contract Description] > ")

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


def ImportMultiSigContractAddr(wallet, args):
    if len(args) < 4:
        print("please specify multisig contract like such: 'import multisig_addr {pubkey in wallet} {minimum # of signatures required} {signing pubkey 1} {signing pubkey 2}...'")
        return

    if wallet is None:
        print("please open a wallet")
        return

    pubkey = get_arg(args, 0)
    m = get_arg(args, 1)
    publicKeys = args[2:]

    if publicKeys[1]:
        pubkey_script_hash = Crypto.ToScriptHash(pubkey, unhex=True)

        verification_contract = Contract.CreateMultiSigContract(pubkey_script_hash, int(m), publicKeys)

        address = verification_contract.Address

        wallet.AddContract(verification_contract)

        print("Added multi-sig contract address %s to wallet" % address)
        return address

    return 'Hello'
