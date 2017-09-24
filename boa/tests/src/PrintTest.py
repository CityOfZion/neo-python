
from boa.code.builtins import list,range
from neo.SmartContract.Framework.Neo.Runtime import Log,Notify

def Main():

    print("holla?") # using pythonic print(), this is tranlated to Neo.Runtime.Log
    start = 4
    stop = 9

    r = range(start,stop)

    Log("hellllllllloo") # using built in Neo.Runtime.Log( this is the same as print(message) )

    Notify(start)   # using the Neo.Runtime.Notify ( this is for logging variables... )

    l = list(length=stop)

    l[3] = 17

    b = r[3]
    print("hullo")

    return b




