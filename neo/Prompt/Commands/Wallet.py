from neo.Core.Blockchain import Blockchain
from neo.Wallets.NEP5Token import NEP5Token
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_asset_id, get_from_addr, get_arg
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from neocore.Cryptography.Crypto import Crypto
from prompt_toolkit import prompt
import binascii
import json
import math


def DeleteAddress(prompter, wallet, addr):

    scripthash = wallet.ToScriptHash(addr)

    success, coins = wallet.DeleteAddress(scripthash)

    if success:
        print("Deleted address %s " % addr)

    else:
        print("error deleting addr %s " % addr)

    return success


def DeleteToken(wallet, contract_hash):

    hash = UInt160.ParseString(contract_hash)

    success = wallet.DeleteNEP5Token(hash)

    if success:
        print("Deleted token %s " % contract_hash)

    else:
        print("error deleting token %s " % contract_hash)

    return False


def ImportWatchAddr(wallet, addr):

    if wallet is None:
        print("Please open a wallet")
        return False

    script_hash = None
    try:
        script_hash = wallet.ToScriptHash(addr)
    except Exception as e:
        pass

    if not script_hash:
        try:
            data = bytearray(binascii.unhexlify(addr.encode('utf-8')))
            data.reverse()
            script_hash = UInt160(data=data)
        except Exception as e:
            pass

    if script_hash:
        wallet.AddWatchOnly(script_hash)
        print("added watch address")
    else:
        print("incorrect format for watch address")


def ImportToken(wallet, contract_hash):

    if wallet is None:
        print("please open a wallet")
        return False

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token(script=hex_script)

        result = token.Query()

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


def ClaimGas(wallet, require_password=True, args=None):

    if args:
        params, from_addr_str = get_from_addr(args)
    else:
        params = None
        from_addr_str = None

    unclaimed_coins = wallet.GetUnclaimedCoins()

    unclaimed_count = len(unclaimed_coins)
    if unclaimed_count == 0:
        print("no claims to process")
        return False

    max_coins_per_claim = None
    if params:
        max_coins_per_claim = get_arg(params, 0, convert_to_int=True)
        if not max_coins_per_claim:
            print("max_coins_to_claim must be an integer")
            return False
        if max_coins_per_claim <= 0:
            print("max_coins_to_claim must be greater than zero")
            return False
    if max_coins_per_claim and unclaimed_count > max_coins_per_claim:
        unclaimed_coins = unclaimed_coins[:max_coins_per_claim]

    unclaimed_coin_refs = [coin.Reference for coin in unclaimed_coins]

    available_bonus = Blockchain.Default().CalculateBonusIgnoreClaimed(unclaimed_coin_refs)

    if available_bonus == Fixed8.Zero():
        print("No gas to claim")
        return False

    claim_tx = ClaimTransaction()
    claim_tx.Claims = unclaimed_coin_refs
    claim_tx.Attributes = []
    claim_tx.inputs = []

    script_hash = wallet.GetChangeAddress()

    # the following can be used to claim gas that is in an imported contract_addr
    # example, wallet claim --from-addr={smart contract addr}
    if from_addr_str:
        script_hash = wallet.ToScriptHash(from_addr_str)
        standard_contract = wallet.GetStandardAddress()
        claim_tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                    data=standard_contract.Data)]

    claim_tx.outputs = [
        TransactionOutput(AssetId=Blockchain.SystemCoin().Hash, Value=available_bonus, script_hash=script_hash)
    ]

    context = ContractParametersContext(claim_tx)
    wallet.Sign(context)

    print("\n---------------------------------------------------------------")
    print("Will make claim for %s GAS" % available_bonus.ToString())
    if max_coins_per_claim and unclaimed_count > max_coins_per_claim:
        print("NOTE: You are claiming GAS on %s unclaimed coins. %s additional claim transactions will be required to claim all available GAS." % (max_coins_per_claim, math.floor(unclaimed_count / max_coins_per_claim)))
    print("------------------------------------------------------------------\n")

    if require_password:
        print("Enter your password to complete this claim")

        passwd = prompt("[Password]> ", is_password=True)

        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return

    if context.Completed:

        claim_tx.scripts = context.GetScripts()

        print("claim tx: %s " % json.dumps(claim_tx.ToJson(), indent=4))

        relayed = NodeLeader.Instance().Relay(claim_tx)

        if relayed:
            print("Relayed Tx: %s " % claim_tx.Hash.ToString())
            wallet.SaveTransaction(claim_tx)
        else:

            print("Could not relay tx %s " % claim_tx.Hash.ToString())
        return claim_tx, relayed

    else:

        print("could not sign tx")

    return None, False


def ShowUnspentCoins(wallet, args):

    addr = None
    asset_type = None
    watch_only = 0
    try:
        for item in args:
            if len(item) == 34:
                addr = wallet.ToScriptHash(item)
            elif len(item) > 1:
                asset_type = get_asset_id(wallet, item)
            if item == '--watch':
                watch_only = 64

    except Exception as e:
        print("Invalid arguments specified")

    if asset_type:
        unspents = wallet.FindUnspentCoinsByAsset(asset_type, from_addr=addr, watch_only_val=watch_only)
    else:
        unspents = wallet.FindUnspentCoins(from_addr=addr, watch_only_val=watch_only)

    for unspent in unspents:
        print('\n-----------------------------------------------')
        print(json.dumps(unspent.ToJson(), indent=4))
        print(unspent.RefToBytes())
