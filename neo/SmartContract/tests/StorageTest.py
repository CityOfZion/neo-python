from boa.code.builtins import range, concat
from boa.blockchain.vm.Neo.Storage import GetContext, Get, Put, Delete


def Main(operation, key, value):

    context = GetContext()

    if operation == 'put':

        Put(context, key, value)

        return True

    if operation == 'put_and_get':

        Put(context, key, value)

        item = Get(context, key)

        return item

    if operation == 'put_5':

        for i in range(0, 5):
            new_key = concat(key, i)
            Put(context, new_key, value)

        return True

    return False
