from neo.SmartContract.Framework.FunctionCode import FunctionCode



def Main():

    a = 1

    c = 3

    a += c

    b = 10

    b -= a


    d = 2

    b *= d

    b /= c

    b %= 3

    f = b + 20

    #f |= 34 # this doesn't curretly work

    return f # expect 21
