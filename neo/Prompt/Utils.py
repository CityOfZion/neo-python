import binascii
from neo.BigInteger import BigInteger


def parse_param(p, ignore_int=False, prefer_hex=True):

    if not ignore_int:
        try:
            val = int(p)
            out = BigInteger(val)
            return out
        except Exception as e:
            pass

    try:
        val = eval(p)

        if type(val) is bytearray:
            return val.hex()

        return val
    except Exception as e:
        pass

    if type(p) is str:
        if prefer_hex:
            return binascii.hexlify( p.encode('utf-8'))
        else:
            return p.encode('utf-8')


    return p