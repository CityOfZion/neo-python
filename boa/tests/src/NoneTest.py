from neo.SmartContract.Framework.FunctionCode import FunctionCode


def Main():

    a = None # this gets coerced to 0


    b = 1

    if a is None: # this evaluates to true ( which it is )
        b = 2

    c = a + b # this evaluates to b + 0, so in this case 2

    #in python, the expected behavior for this would be to raise
    #a type error, since you can't add NoneType to an int
    #in the vm, its all ok i guess

    return c

