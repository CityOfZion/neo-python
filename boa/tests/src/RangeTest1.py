
from boa.code.builtins import list
from neo.SmartContract.Framework.Neo.Runtime import Notify
def Main():

    start = 4
    stop = 9 #int

#    out = [10,2, 3, 4, 6, 7]



    length = stop - start


    out = list(length=length)

    index = 0
    orig_start = start

    while start < stop:
        val = index + orig_start
        out[index] = val
        index = index + 1
        start = orig_start + index

        Notify(start)

        #d = stuff(1, 2) # this doesn't work at the moment


    return out[4]




def stuff(a, b):

    out = a + b
    return out