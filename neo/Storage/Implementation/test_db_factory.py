from DBFactory import getBlockchainDB
import test2


_db = getBlockchainDB()

# _db.write(b'1', b'first')

ret_1 = test2.db2.get(b'1')
ret_default = _db.get(b'2', b'default_value')

print(ret_1, ret_default)
assert ret_1 == b'first'
assert ret_default == b'default_value'

