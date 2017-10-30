import binascii
from neo.BigInteger import BigInteger
from neo.Fixed8 import Fixed8
from neo.Core.Helper import Helper

def get_asset_attachments(params):

    to_remove = []
    neo_to_attach = None
    gas_to_attach = None

    for item in params:

        if type(item) is str:
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


def get_from_addr(params):
    to_remove = []
    from_addr = None
    for item in params:
        if '--from-addr=' in item:
            to_remove.append(item)
            try:
                from_addr = item.replace('--from-addr=', '')
            except Exception as e:
                pass
    for item in to_remove:
        params.remove(item)


    return params, from_addr


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

        # check for address strings like 'ANE2ECgA6YAHR5Fh2BrSsiqTyGb5KaS19u' and
        # convert them to a bytearray
        if len(p) == 34 and p[0] == 'A':
            addr = Helper.AddrStrToScriptHash(p).Data
            return addr

        if prefer_hex:
            return binascii.hexlify( p.encode('utf-8'))
        else:
            return p.encode('utf-8')


    return p



def get_arg(arguments, index=0, convert_to_int=False, do_parse=False):
    try:
        arg = arguments[index]
        if convert_to_int:
            return int(arg)
        if do_parse:
            return parse_param(arg)
        return arg
    except Exception as e:
        pass
    return None
