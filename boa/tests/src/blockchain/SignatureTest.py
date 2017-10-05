from boa.code.builtins import verify_signature
from boa.blockchain.vm.Neo.Runtime import CheckWitness,Notify



PUBKEY = b'\x02\xf7\xbchi\xdf-\xbew\xa6bE\x11\x16\xcc\x99\x9cx\xc3^\xedA\xa11c\x17\xa3\xef\xe3c@t2'


#this is the ScriptHash of the address that created the contract
#the hex string is b'f223483e4287bd7c3e85a7ca896943179cbbc246'
#the below is the hex version unhexxed and reversed

OWNER = b'a\xc2\xbb\x9c\x17Ci\x89\xca\xa7\x85>|\xbd\x87B>H#\xf2'

def Main():

    verify = CheckWitness(OWNER)

    j = 0

    if verify:
        j = 1
        DoOk()
    else:
        j = 2
        DoNotOk()

    return j


def DoOk():

    print("doing ok!!")


def DoNotOk():

    print("doing not ok")
