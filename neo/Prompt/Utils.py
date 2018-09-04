import binascii
from neocore.BigInteger import BigInteger
from neocore.Fixed8 import Fixed8
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Wallets.Coin import CoinState
from neo.Core.TX.Transaction import TransactionInput
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameter import ContractParameterType
from neocore.UInt256 import UInt256
from neocore.Cryptography.ECCurve import ECDSA
from decimal import Decimal
from logzero import logger
import json
from prompt_toolkit.shortcuts import PromptSession


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


def get_owners_from_params(params):
    to_remove = []
    owners = None

    for item in params:
        if type(item) is str:
            if '--owners=' in item:
                owners = []
                to_remove.append(item)
                try:
                    owner_list = eval(item.replace('--owners=', ''))
                    owners = set()
                    for o in owner_list:
                        shash = Helper.AddrStrToScriptHash(o)
                        owners.add(shash)
                except Exception as e:
                    logger.info("Could not parse owner %s " % e)
                    pass
    for item in to_remove:
        params.remove(item)

    return params, owners


def get_asset_id(wallet, asset_str):
    assetId = None

    # check to see if this is a token
    for token in wallet.GetTokens().values():
        if asset_str == token.symbol:
            return token
        elif asset_str == token.ScriptHash.ToString():
            return token

    if asset_str.lower() == 'neo':
        assetId = Blockchain.Default().SystemShare().Hash
    elif asset_str.lower() == 'gas':
        assetId = Blockchain.Default().SystemCoin().Hash
    elif Blockchain.Default().GetAssetState(asset_str):
        assetId = Blockchain.Default().GetAssetState(asset_str).AssetId

    return assetId


def get_asset_amount(amount, assetId):
    f8amount = Fixed8.TryParse(amount)
    if f8amount is None:
        print("invalid amount format")

    elif f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
        print("incorrect amount precision")
        return None

    return f8amount


def get_withdraw_from_watch_only(wallet, scripthash_from):
    withdraw_from_watch_only = 0
    # check to see if contract address is in the wallet
    wallet_contract = wallet.GetContract(scripthash_from)

    # if it is not, check to see if it in the wallet watch_addr
    if wallet_contract is None:
        if scripthash_from in wallet._watch_only:
            withdraw_from_watch_only = CoinState.WatchOnly
            wallet_contract = scripthash_from

    if wallet_contract is None:
        print("please add this contract into your wallet before withdrawing from it")
        print("Use import watch_addr {ADDR}, then rebuild your wallet")
        return None

    return withdraw_from_watch_only


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


def get_fee(params):
    to_remove = []
    fee = None
    for item in params:
        if '--fee=' in item:
            to_remove.append(item)
            try:
                fee = get_asset_amount(item.replace('--fee=', ''), Blockchain.SystemCoin().Hash)
            except Exception as e:
                pass
    for item in to_remove:
        params.remove(item)

    return params, fee


def get_parse_addresses(params):
    if '--no-parse-addr' in params:
        params.remove('--no-parse-addr')
        return params, False
    return params, True


def get_tx_attr_from_args(params):
    to_remove = []
    tx_attr_dict = []
    for item in params:
        if '--tx-attr=' in item:
            to_remove.append(item)
            try:
                attr_str = item.replace('--tx-attr=', '')

                # this doesn't work for loading in bytearrays
                #                tx_attr_obj = json.loads(attr_str)
                tx_attr_obj = eval(attr_str)
                if type(tx_attr_obj) is dict:
                    if attr_obj_to_tx_attr(tx_attr_obj) is not None:
                        tx_attr_dict.append(attr_obj_to_tx_attr(tx_attr_obj))
                elif type(tx_attr_obj) is list:
                    for obj in tx_attr_obj:
                        if attr_obj_to_tx_attr(obj) is not None:
                            tx_attr_dict.append(attr_obj_to_tx_attr(obj))
                else:
                    logger.error("Invalid transaction attribute specification: %s " % type(tx_attr_obj))
            except Exception as e:
                logger.error("Could not parse json from tx attrs: %s " % e)
    for item in to_remove:
        params.remove(item)

    return params, tx_attr_dict


def attr_obj_to_tx_attr(obj):
    try:
        datum = obj['data']
        if type(datum) is str:
            datum = datum.encode('utf-8')
        usage = obj['usage']
        if usage == TransactionAttributeUsage.Script and len(datum) == 40:
            datum = binascii.unhexlify(datum)
        return TransactionAttribute(usage=usage, data=datum)
    except Exception as e:
        logger.error("could not convert object %s into TransactionAttribute: %s " % (obj, e))
    return None


def parse_param(p, wallet=None, ignore_int=False, prefer_hex=True, parse_addr=True):
    # first, we'll try to parse an array
    try:
        items = eval(p, {"__builtins__": {'list': list}}, {})
        if len(items) > 0 and type(items) is list:

            parsed = []
            for item in items:
                parsed.append(parse_param(item, wallet, parse_addr=parse_addr))
            return parsed

    except Exception as e:
        #        print("Could not eval items as array %s " % e)
        pass

    if not ignore_int:
        try:
            val = int(p)
            out = BigInteger(val)
            return out
        except Exception as e:
            pass

    try:
        val = eval(p, {"__builtins__": {'bytearray': bytearray, 'bytes': bytes, 'list': list}}, {})
        if type(val) is bytearray:
            return val
        elif type(val) is bytes:
            # try to unhex
            try:
                val = binascii.unhexlify(val)
            except Exception as e:
                pass
            # now it should be unhexxed no matter what, and we can hex it
            return val.hex().encode('utf-8')
        elif type(val) is bool:
            return val

    except Exception as e:
        pass

    if type(p) is str:

        if wallet is not None:
            for na in wallet.NamedAddr:
                if na.Title == p:
                    return bytearray(na.ScriptHash)

        # check for address strings like 'ANE2ECgA6YAHR5Fh2BrSsiqTyGb5KaS19u' and
        # convert them to a bytearray
        if parse_addr and len(p) == 34 and p[0] == 'A':
            addr = Helper.AddrStrToScriptHash(p).Data
            return addr

        if prefer_hex:
            return binascii.hexlify(p.encode('utf-8'))
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


def lookup_addr_str(wallet, addr):
    for alias in wallet.NamedAddr:
        if addr == alias.Title:
            return alias.UInt160ScriptHash()
    try:
        script_hash = wallet.ToScriptHash(addr)
        return script_hash
    except Exception as e:
        print(e)


def parse_hold_vins(results):
    holds = results[0].GetByteArray()
    holdlen = len(holds)
    numholds = int(holdlen / 33)

    vins = []
    for i in range(0, numholds):
        hstart = i * 33
        hend = hstart + 33
        item = holds[hstart:hend]

        vin_index = item[0]
        vin_tx_id = UInt256(data=item[1:])

        t_input = TransactionInput(prevHash=vin_tx_id, prevIndex=vin_index)

        vins.append(t_input)

    return vins


def string_from_fixed8(amount, decimals):
    precision_mult = pow(10, decimals)
    amount = Decimal(amount) / Decimal(precision_mult)
    formatter_str = '.%sf' % decimals
    amount_str = format(amount, formatter_str)

    return amount_str


def get_input_prompt(message):
    from neo.bin.prompt import PromptInterface

    return PromptSession(completer=PromptInterface.prompt_completer,
                         history=PromptInterface.history).prompt(message)


def gather_param(index, param_type, do_continue=True):
    ptype = ContractParameterType(param_type)
    prompt_message = '[Param %s] %s input: ' % (index, ptype.name)

    try:

        result = get_input_prompt(prompt_message)

        if ptype == ContractParameterType.String:
            return str(result), False
        elif ptype == ContractParameterType.Integer:
            return int(result), False
        elif ptype == ContractParameterType.Boolean:
            return bool(result), False
        elif ptype == ContractParameterType.PublicKey:
            return ECDSA.decode_secp256r1(result).G, False
        elif ptype == ContractParameterType.ByteArray:
            if isinstance(result, str) and len(result) == 34 and result[0] == 'A':
                return Helper.AddrStrToScriptHash(result).Data, False
            res = eval(result, {"__builtins__": {'bytearray': bytearray, 'bytes': bytes}}, {})
            if isinstance(res, bytes):
                return bytearray(res), False
            return res, False

        elif ptype == ContractParameterType.Array:
            res = eval(result)
            if isinstance(res, list):
                return res, False
            raise Exception("Please provide a list")
        else:
            raise Exception("Unknown param type %s " % ptype.name)

    except KeyboardInterrupt:  # Control-C pressed: exit

        return None, True

    except Exception as e:

        print("Could not parse param as %s : %s " % (ptype, e))
        if do_continue:
            return gather_param(index, param_type, do_continue)

    return None, True
