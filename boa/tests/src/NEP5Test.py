from boa.blockchain.vm.Neo.Runtime import Log
from boa.blockchain.vm.System.ExecutionEngine import GetScriptContainer,GetExecutingScriptHash
from boa.blockchain.vm.Neo.Transaction import *
from boa.blockchain.vm.Neo.Output import *
from boa.blockchain.vm.Neo.Blockchain import GetHeight,GetHeader
from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import GetTrigger,CheckWitness
from boa.blockchain.vm.Neo.TriggerType import Application,Verification
from boa.blockchain.vm.Neo.Storage import GetContext,Get,Put,Delete

from boa.code.builtins import verify_signature

#-------------------------------------------
# ICO SETTINGS
#-------------------------------------------

TOKEN_NAME ='PyToken'
SYMBOL = 'BOA'

OWNER = b'F\xc2\xbb\x9c\x17Ci\x89\xca\xa7\x85>|\xbd\x87B>H#\xf2'

DECIMALS=8

FACTOR = 100000000


#-------------------------------------------
# ICO SETTINGS
#-------------------------------------------

NEO_ASSET_ID = b'\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5'

# 5million times decimals ( factor )
TOTAL_AMOUNT = 500000000000000

PRE_ICO_CAP = 100000000 # this is FACTOR

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
            return Deploy()
        elif operation == 'mintTokens':
            return MintTokens()
        elif operation == 'totalSupply':
            return TotalSupply()
        elif operation == 'name':
            return Name()
        elif operation == 'decimals':
            return Decimals()
        elif operation == 'symbol':
            return Symbol()

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

                return BalanceOf(account)

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

    if len(references) < 1:
        print("no neo attached")
        return False

    reference = references[0]

    sender = reference.ScriptHash

    value = 0

    if reference.AssetId == NEO_ASSET_ID:

        receiver = GetExecutingScriptHash()

        for output in tx.Outputs:
            if output.ScriptHash == receiver:
                value = value + output.Value

        rate = CurrentSwapRate()

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

    context = GetContext()

    balance = Get(context, account)

    return balance


def CurrentSwapRate():

    basic = 1000 * FACTOR
    duration = ICO_END_TIME - ICO_START_TIME

    context = GetContext()

    total_supply = Get(context, 'totalSupply')

    if total_supply >= TOTAL_AMOUNT:
        return False

    currentHeight = GetHeight()
    currentBlock  = GetHeader(currentHeight)

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

