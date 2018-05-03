from boa.interop.Neo.Storage import GetContext, Get

ctx = GetContext()


def Main(key):

    return Get(ctx, key)

#
# Put(ctx, 'i1', 1)
# Put(ctx, 'i2', 2)
# Put(ctx, 'i3', -3)
# Put(ctx, 'i4', 400000000000)
#
# Put(ctx, 's1', 'abc')
# Put(ctx, 's2', 'hello world')
# Put(ctx, 's3', 'ok')
#
# Put(ctx, 'b1', b'\x01\x02\x03')
# Put(ctx, 'b2', bytearray(b'\x1a\xff\x0a'))
#
# return True
