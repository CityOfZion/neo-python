from boa.blockchain.vm.Neo.Runtime import Log,Notify
from boa.blockchain.vm.System.ExecutionEngine import GetScriptContainer,GetExecutingScriptHash
from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.Blockchain import GetHeight,GetHeader
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import GetTrigger,CheckWitness
from boa.blockchain.vm.Neo.TriggerType import Application,Verification
from boa.blockchain.vm.Neo.Output import GetScriptHash,GetValue,GetAssetId
from boa.blockchain.vm.Neo.Storage import GetContext,Get,Put,Delete

from boa.code.builtins import verify_signature

#-------------------------------------------
# ICO SETTINGS
#-------------------------------------------

TOKEN_NAME ='LOCALTOKEN'
SYMBOL = 'LWTF'

OWNER = b'F\xc2\xbb\x9c\x17Ci\x89\xca\xa7\x85>|\xbd\x87B>H#\xf2'

DECIMALS=8

FACTOR = 100000000


#-------------------------------------------
# ICO SETTINGS
#-------------------------------------------

NEO_ASSET_ID = b'\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5'

# 5million times decimals ( factor )
TOTAL_AMOUNT = 500000000000000

PRE_ICO_CAP = 1000000000 # amount for the owner to start with

ICO_START_TIME = 1502726400 # August 14 2017
ICO_END_TIME = 1513936000 # December 22 2017

#-------------------------------------------
# Events
#-------------------------------------------

OnTransfer = RegisterAction('transfer', 'from','to','amount')

OnRefund = RegisterAction('refund', 'to','amount')


def Main(operation, args):

    trigger = GetTrigger()

    if trigger == Verification():

        print("doing verification!")
        owner_len = len(OWNER)

        if owner_len == 20:

            res = CheckWitness(OWNER)
            print("owner verify result")
            return res

#        elif owner_len == 33:
#            #res = verify_signature(operation, OWNER)
#            Log("verify signature not understood by me yet")

    elif trigger == Application():

        print("doing application!")

        if operation == 'deploy':
            out = Deploy()
            print("deployed!")
            return out
        elif operation == 'mintTokens':
            domint = MintTokens()
            print("minted token!")
            return domint
        elif operation == 'totalSupply':
            supply = TotalSupply()
            print("got total supply")
            Notify(supply)
            return supply
        elif operation == 'name':
            n = Name()
            return n
        elif operation == 'decimals':
            d = Decimals()
            return d
        elif operation == 'symbol':
            sym = Symbol()
            return sym

        elif operation == 'transfer':
            print("do transfers")
            if len(args) == 3:
                t_from = args[0]
                t_to = args[1]
                t_amount = args[2]
                return DoTransfer(t_from, t_to, t_amount)

            else:
                return False

        elif operation == 'balanceOf':
            if len(args) == 1:

                print("do balance")

                account = args[0]

                balance = BalanceOf(account)
                print("got balance")
                Notify(balance)

                return balance

            else:

                return 0

    return False


def Name():
    print("getting name!")
    return TOKEN_NAME

def Symbol():
    print("getting symbol!")
    return SYMBOL

def Decimals():
    print("getting decimals...")
    return DECIMALS


def Deploy():
    print("deploying!")

    isowner = CheckWitness(OWNER)


    if isowner:

        print("ok to deploy")
        context = GetContext()

        total = Get(context, 'totalSupply')


        if len(total) == 0:

            Log("WILL DEPLOY!")

            Put(context, OWNER, PRE_ICO_CAP)

            Put(context, "totalSupply", PRE_ICO_CAP)

            OnTransfer(0, OWNER, PRE_ICO_CAP)

            return True
        else:
            print("ALREADY DEPLOYED, wont do it again")


    print("only owner can deploy")
    return False

def MintTokens():
    print("minting tokens!")

    tx = GetScriptContainer()

    references = tx.References

    print("helol1")
    if len(references) < 1:
        print("no neo attached")
        return False

    print("hello2")
    reference = references[0]
    print("hello2")
#    sender = reference.ScriptHash

    sender = GetScriptHash(reference)
    print("hello4")

    value = 0
    print("hello5")
    output_asset_id = GetAssetId(reference)
    if output_asset_id == NEO_ASSET_ID:

        print("hello6")
        receiver = GetExecutingScriptHash()
        print("hello7")
        for output in tx.Outputs:
            shash = GetScriptHash(output)
            print("getting shash..")
            if shash == receiver:
                print("adding value?")
                output_val = GetValue(output)
                value = value + output_val

        print("getting rate")
        rate = CurrentSwapRate()
        print("got rate")
        if rate == 0:
            OnRefund(sender, value)
            return False

        num_tokens = value * rate / 100000000


        context = GetContext()

        balance = Get(context, sender)

        new_total = num_tokens + balance

        Put(context, sender, new_total)

        total_supply = Get(context, 'totalSupply')

        new_total_supply = total_supply + num_tokens

        Put(context, 'totalSupply', new_total_supply)

        OnTransfer(0, sender, num_tokens)

        return True


    return False

def TotalSupply():

    print("total supply!")

    context = GetContext()

    res = Get(context, "totalSupply")

    print("got total supply")
    Notify(res)

    return res

def DoTransfer(t_from, t_to, amount):

    if amount <= 0:
        print("cannot transfer zero or less")
        return False

    from_is_sender = CheckWitness(t_from)

    if from_is_sender:

        if t_from == t_to:
            return True

        context = GetContext()

        from_val = Get(context, t_from)

        if from_val < amount:
            print("Insufficient funds")
            return False

        if from_val == amount:
            print("Removing all funds!")
            Delete(context, t_from)

        else:
            difference = from_val - amount
            Put(context, t_from, difference)

        to_value = Get(context, t_to)

        to_total = to_value + amount


        Put(context, t_to, to_total)

        OnTransfer(t_from, t_to, amount)

        return True
    else:
        print("from address is not the tx sender")

    return False

def BalanceOf(account):

    print("getting balance of...")
    context = GetContext()
    print("getting context...")
    balance = Get(context, account)
    print("got balance...")

    return balance


def CurrentSwapRate():

    basic = 1000 * FACTOR
    duration = ICO_END_TIME - ICO_START_TIME
    print("getting swap rate")
    context = GetContext()
    print("got context")

    total_supply = Get(context, 'totalSupply')
    print("got total supply")
    if total_supply >= TOTAL_AMOUNT:
        return False
    print("getting current height...")
    currentHeight = GetHeight()
    print("got current height")
    currentBlock  = GetHeader(currentHeight)
    print("got current block...")
    time = currentBlock.Timestamp - ICO_START_TIME

    if time < 0:

        return 0

    elif time < 86400:
        return basic * 130 / 100

    elif time < 259200:
        return basic * 120 / 100

    elif time < 604800:
        return basic * 110 / 100

    elif time < duration:
        return basic

    return 0

