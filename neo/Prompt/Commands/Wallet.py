

def DeleteAddress(prompter,wallet, addr):


    scripthash = wallet.ToScriptHash(addr)

    success, coins = wallet.DeleteAddress(scripthash)

    if success:
        print("Deleted address %s " % addr)

    else:
        print("error deleting addr %s " % addr)