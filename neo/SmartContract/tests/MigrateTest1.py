from boa.interop.Neo.Storage import GetContext, Get, Put
from boa.interop.Neo.Contract import Migrate, Destroy
from boa.interop.Neo.Runtime import Notify

ctx = GetContext()


def Main(operation, data):

    if operation == 'store_data':

        Put(ctx, 'i1', 1)
        Put(ctx, 'i2', 2)
        Put(ctx, 'i3', -3)
        Put(ctx, 'i4', 400000000000)

        Put(ctx, 's1', 'abc')
        Put(ctx, 's2', 'hello world')
        Put(ctx, 's3', 'ok')

        Put(ctx, 'b1', b'\x01\x02\x03')
        Put(ctx, 'b2', bytearray(b'\x1a\xff\x0a'))

        return True

    elif operation == 'get_data':

        items = []

        items.append(Get(ctx, 'i1'))
        items.append(Get(ctx, 's1'))
        items.append(Get(ctx, 'b1'))

        return items

    elif operation == 'do_migrate':

        print("migrating")

        param_list = bytearray(b'\x07')
        return_type = bytearray(b'\x05')
        properties = 1
        name = 'migrated contract 3'
        version = '0.3'
        author = 'localhuman3'
        email = 'nex@email.com'
        description = 'test migrate3'

        new_contract = Migrate(data, param_list, return_type, properties, name, version, author, email, description)

        return new_contract

    elif operation == 'do_destroy':

        Destroy()

        return True

    return False
