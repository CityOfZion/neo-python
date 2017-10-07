from boa.code.builtins import verify_signature
from boa.blockchain.vm.Neo.Runtime import CheckWitness,Notify



OWNER_PUBKEY = b'\x02\xf7\xbchi\xdf-\xbew\xa6bE\x11\x16\xcc\x99\x9cx\xc3^\xedA\xa11c\x17\xa3\xef\xe3c@t2'


#this is the ScriptHash of the address that created the contract
#the hex string is b'f223483e4287bd7c3e85a7ca896943179cbbc246'
#the below is the hex version unhexxed and reversed

OWNER_HASH = b'F\xc2\xbb\x9c\x17Ci\x89\xca\xa7\x85>|\xbd\x87B>H#\xf2'

def Main(operation):

    verify = CheckWitness(OWNER_HASH)


    if verify:
        print("ok!!")
    else:
        print("not ok!")



    Notify(operation)


    verify2 = verify_signature(operation, OWNER_PUBKEY) # not sure of how this works

    Notify(verify2) # it returs false for now


    return True