from boa.builtins import range, concat
from boa.interop.Neo.Storage import GetContext, Get, Put


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

    if operation == 'put_9':

        for i in range(0, 9):
            new_key = concat(key, i)
            Put(context, new_key, value)

        return True

    return False
