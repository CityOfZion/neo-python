from neo.Core.Blockchain import Blockchain
from neo.Wallets.NEP5Token import NEP5Token
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Core.TX.Transaction import TransactionOutput
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import string_from_fixed8
from neo.Fixed8 import Fixed8
from prompt_toolkit import prompt
import binascii
import json


def DeleteAddress(prompter, wallet, addr):

    scripthash = wallet.ToScriptHash(addr)

    success, coins = wallet.DeleteAddress(scripthash)

    if success:
        print("Deleted address %s " % addr)

    else:
        print("error deleting addr %s " % addr)

    return success


def DeleteToken(wallet, contract_hash):

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token(script=hex_script)

        success = wallet.DeleteNEP5Token(token)

        if success:
            print("Deleted token %s " % contract_hash)

        else:
            print("error deleting token %s " % contract_hash)
    else:
        print("Contract %s not found " % contract_hash)

    return False


def ImportWatchAddr(wallet, addr):

    if wallet is None:
        print("Please open a wallet")
        return False

    script_hash = wallet.ToScriptHash(addr)

    result = wallet.AddWatchOnly(script_hash)

    return result


def ImportToken(wallet, contract_hash):

    if wallet is None:
        print("please open a wallet")
        return False

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token(script=hex_script)

        result = token.Query(wallet)

        if result:

            wallet.AddNEP5Token(token)
            print("added token %s " % json.dumps(token.ToJson(), indent=4))

        else:

            print("Could not import token")


def AddAlias(wallet, addr, title):
    if wallet is None:
        print("Please open a wallet")
        return False
    try:
        script_hash = wallet.ToScriptHash(addr)
        wallet.AddNamedAddress(script_hash, title)
    except Exception as e:
        print(e)


def ClaimGas(wallet, require_password=True):

    unclaimed_coins = wallet.GetUnclaimedCoins()
    unclaimed_coin_refs = [coin.Reference for coin in unclaimed_coins]

    if len(unclaimed_coin_refs) == 0:
        print("no claims to process")
        return False

    available_bonus = Blockchain.Default().CalculateBonusIgnoreClaimed(unclaimed_coin_refs)

    if available_bonus == Fixed8.Zero():

        print("No gas to claim")
        return False

    claim_tx = ClaimTransaction()
    claim_tx.Claims = unclaimed_coin_refs
    claim_tx.Attributes = []
    claim_tx.inputs = []
    claim_tx.outputs = [
        TransactionOutput(AssetId=Blockchain.SystemCoin().Hash, Value=available_bonus, script_hash=wallet.GetChangeAddress())
    ]

    context = ContractParametersContext(claim_tx)
    wallet.Sign(context)

    print("\n---------------------------------------------------------------")
    print("Will make claim for %s GAS" % available_bonus.ToString())
    print("------------------------------------------------------------------\n")

    if require_password:
        print("Enter your password to complete this claim")

        passwd = prompt("[Password]> ", is_password=True)

        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return

    if context.Completed:

        claim_tx.scripts = context.GetScripts()
        wallet.SaveTransaction(claim_tx)

        relayed = NodeLeader.Instance().Relay(claim_tx)

        if relayed:
            print("Relayed Tx: %s " % claim_tx.Hash.ToString())
        else:

            print("Could not relay tx %s " % claim_tx.Hash.ToString())
        return claim_tx, relayed

    else:

        print("could not sign tx")

    return None, False


def ShowUnspentCoins(wallet, address=None):

    addr = None
    try:
        if len(address) > 0:
            addr_str = address[0]
            addr = wallet.ToScriptHash(addr_str)
    except Exception as e:
        print("Invalid address specified")

    unspents = wallet.FindUnspentCoins(from_addr=addr)

    jsn = [unspent.ToJson() for unspent in unspents]

    print(json.dumps(jsn, indent=4))
