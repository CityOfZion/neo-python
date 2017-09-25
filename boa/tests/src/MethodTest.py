from boa.blockchain.vm.Neo.Runtime import Log,Notify
from boa.code.builtins import list

def Main():

    a = 1

    b = [1,2,34]

    b1 = b[0]
    b2= b[1]
    c = add3(b1, b2)

    d = addd(a, c)
    print("will return")
    return a + c + d


def addd(a, b):

    result = a + b
    print("addd")
    res2 = stuff()
    Log("add loggg")
    res3 = add3(result, res2)

    print("res 3 is...")
    Notify(res3)

    return result + stuff() + res2 + res3

def stuff():

    a = 4

    b = 2

    items = [0,1,0,9,20, 4,23]

    j = items[3]

    q = n_range(1, 10)

    return a + b + j + items[1] + q[4]

def add3(a, b):

    print("add3")

    print("add 3 loggg")
    return a + b


def n_range(start, stop):
    """
    range(start, stop) -> list object

    Return an list that is a a sequence of integers from start (inclusive)
    to stop (exclusive).  range(i, j) produces i, i+1, i+2, ..., j-1.
    """

#    out = []

#    if start >= stop:
#        return out

    length = stop - start

    out = list(length=length)

    index = 0
    orig_start = start

    while start < stop:
        val = index + orig_start
        out[index] = val
        index = index + 1
        start = orig_start + index

    return out