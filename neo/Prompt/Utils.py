import binascii
from neo.BigInteger import BigInteger
from neo.Fixed8 import Fixed8


def get_asset_attachments(params):

    to_remove = []
    neo_to_attach = None
    gas_to_attach = None
    for item in params:
        if '--attach-neo=' in item:
            to_remove.append(item)
            try:
                neo_to_attach = Fixed8.TryParse(int(item.replace('--attach-neo=', '')))
            except Exception as e:
                pass
        if '--attach-gas=' in item:
            to_remove.append(item)
            try:
                gas_to_attach = Fixed8.FromDecimal(float(item.replace('--attach-gas=', '')))
            except Exception as e:
                pass
    for item in to_remove:
        params.remove(item)


    return params, neo_to_attach, gas_to_attach


def parse_param(p, ignore_int=False, prefer_hex=True):

#    print("parsing param: %s " % p)

#    pdb.set_trace()

    #first, we'll try to parse an array
    try:
        items = eval(p)
        if len(items) > 0 and type(items) is list:

            parsed = []
            for item in items:
                parsed.append(parse_param(item))
            return parsed

    except Exception as e:
#        print("couldnt eval items as array %s " % e)
        pass

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



def get_arg(arguments, index=0, convert_to_int=False):
    try:
        arg = arguments[index]
        if convert_to_int:
            return int(arg)
        return arg
    except Exception as e:
        pass
    return None
