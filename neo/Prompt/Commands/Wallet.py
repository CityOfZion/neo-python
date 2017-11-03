from neo.Core.Blockchain import Blockchain
from neo.Wallets.NEP5Token import NEP5Token
import binascii
import json

def DeleteAddress(prompter, wallet, addr):

    scripthash = wallet.ToScriptHash(addr)

    success, coins = wallet.DeleteAddress(scripthash)

    if success:
        print("Deleted address %s " % addr)

    else:
        print("error deleting addr %s " % addr)


def ImportWatchAddr(wallet, addr):

    if wallet is None:
        print("Please open a wallet")
        return False

    script_hash = wallet.ToScriptHash(addr)

    result = wallet.AddWatchOnly(script_hash)

    print("result %s " % result)


def ImportToken(wallet, contract_hash):

    if wallet is None:
        print("please open a wallet")
        return False

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token(script= hex_script)

        result = token.Query(wallet)

        if result:

            print("queried token %s " % json.dumps(token.ToJson(), indent=4))

            wallet.AddNEP5Token(token)

        else:

            print("Could not import token")



