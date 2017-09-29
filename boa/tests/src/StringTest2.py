from boa.code.builtins import concat
from boa.blockchain.vm.Neo.Runtime import Notify

def Main():


    mystring = 'abcdefgh'
    count = 3
    mys = mystring[0:count]

    strmy = mystring[4:]

    Notify(mys)
    Notify(strmy)


    myarray = [b'\x10',b'\x20',b'\x30',b'\x40']

    #mr1 = myarray[0:2] this does not work, need to implement a bytearray thing of some sort
    #Notify(mr1)

    return 1