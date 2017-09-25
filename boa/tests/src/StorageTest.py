from neo.SmartContract.Framework.Neo.Storage import Get,Put,Delete,GetContext
from neo.SmartContract.Framework.Neo.Runtime import Notify

def Main():

    context = GetContext()

    print("hello")
    Notify(context)

    item_key = 'hello'
    item_val = 'hhhhhhh'
    Notify(item_val)
    Put(context, item_key, item_val)
    print("hhhh")
    a = 1

    out = Get(context, item_key)



    return out
