from neo.SmartContract.Framework.FunctionCode import FunctionCode

from boa.code.builtins import list

def Main():

    start = 4
    stop = 9

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


    return out[4]




