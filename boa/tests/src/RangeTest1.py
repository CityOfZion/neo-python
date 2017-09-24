
from boa.code.builtins import list

def Main():

    start = 4
    stop = 9 #int

#    out = [10,2, 3, 4, 6, 7]



    length = stop - start


    out = list(length=length)

    index = 0
    orig_start = start

    while start + orig_start < stop:
        val = index + orig_start
        out[index] = val
        index = index + 1
        start = orig_start + index


    return out[4]




