

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

    print("will import watch address %s %s " % (addr, script_hash))

    result = wallet.AddWatchOnly(script_hash)

    print("result %s " % result)
