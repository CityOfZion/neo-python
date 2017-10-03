
from boa.blockchain.vm.Neo.Runtime import Log,Notify
from boa.code.builtins import concat

def Main(ba1, ba2):

#    b = ba2

    #m = ba2[1] # subscribt for a byte array does not work

    m = ba2[1:2] # but you can do this instead

    #strings and byte arrays work the same
    mystr = 'staoheustnau'

    #this will not work
    #m = mystr[3]

    #but this will
    m = mystr[3:5]

    #
    m = ba1[1:]

    return concat(mystr, ba2)