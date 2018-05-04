from boa.interop.Neo.Storage import GetContext, Get
from boa.interop.Neo.Runtime import Notify
ctx = GetContext()


def Main(key):

    print("hello")

    Notify(key)

    val = Get(ctx, key)

    return val
