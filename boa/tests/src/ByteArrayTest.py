
from boa.blockchain.vm.Neo.Runtime import Log,Notify
from boa.code.builtins import concat

def Main():

    c = b'\x01\x04\xaf\x09'

    l = len(c)

    b = c[2:l]

    j = b'\x01\x02\x03\x04\x05\x06\x07'

    k = concat(c, j)


    m = k[3:6]

    return concat(m, b)