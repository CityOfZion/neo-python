# -*- coding:utf-8 -*-
"""
Description:
    Cryptography Helper
Usage:
    from neo.Cryptography.Helper import *
"""

from bitcoin import *
import os
import time
import random
import hashlib
import binascii
import base58


def hash_to_wallet_address(ba, address_version=23):
    """
    Translate script hash into the public address.

    Args:
        ba (bytes): script hash.
        address_version: fixed to 23. Defined in https://github.com/neo-project/neo/blob/master/neo/protocol.json

    Returns:
        str: base58 encoded string representing the wallet address.
    """
    sb = bytearray([23]) + ba
    c256 = bin_dbl_sha256(sb)[0:4]
    outb = sb + bytearray(c256)
    return base58.b58encode(bytes(outb))


long = int


def double_sha256(ba):
    """
    Perform two SHA256 operations on the input.

    Args:
        ba (bytes): data to hash.

    Returns:
        str: hash as a double digit hex string.
    """
    d1 = hashlib.sha256(ba)
    d2 = hashlib.sha256()
    d1.hexdigest()
    d2.update(d1.digest())
    return d2.hexdigest()


def pubkey_to_redeem(pubkey):
    """
    Convert the public key to the redeemscript format.

    Args:
        pubkey (bytes): public key.

    Returns:
        bytes: redeemscript.
    """
    return binascii.unhexlify(b'21' + pubkey) + from_int_to_byte(int(b'ac', 16))


def redeem_to_scripthash(redeem):
    """
    Convert a redeem script to a script hash.

    Args:
        redeem (bytes):

    Returns:
        bytes: script hash.
    """
    return binascii.hexlify(bin_hash160(redeem))


def scripthash_to_address(scripthash):
    """
    Convert a script hash to a public address.

    Args:
        scripthash (bytes):

    Returns:
        str: base58 encoded string representing the wallet address.
    """
    return bin_to_b58check(binascii.unhexlify(scripthash), 23)


def pubkey_to_pubhash(pubkey):
    """
    Convert a public key to a script hash.

    Args:
        pubkey (bytes):

    Returns:
        bytes: script hash.
    """
    return redeem_to_scripthash(pubkey_to_redeem(pubkey))


# Extended Euclidean Algorithm
def inv(a, n):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def from_jacobian(p):
    z = inv(p[2], P)
    return ((p[0] * z ** 2) % P, (p[1] * z ** 3) % P)


def jacobian_double(p):
    if not p[1]:
        return (0, 0, 0)
    ysq = (p[1] ** 2) % P
    S = (4 * p[0] * ysq) % P
    M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
    nx = (M ** 2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq ** 2) % P
    nz = (2 * p[1] * p[2]) % P
    return (nx, ny, nz)


def jacobian_add(p, q):
    if not p[1]:
        return q
    if not q[1]:
        return p
    U1 = (p[0] * q[2] ** 2) % P
    U2 = (q[0] * p[2] ** 2) % P
    S1 = (p[1] * q[2] ** 3) % P
    S2 = (q[1] * p[2] ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return (0, 0, 1)
        return jacobian_double(p)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R ** 2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * p[2] * q[2]) % P
    return (nx, ny, nz)


def jacobian_multiply(a, n):
    if a[1] == 0 or n == 0:
        return (0, 0, 1)
    if n == 1:
        return a
    if n < 0 or n >= N:
        return jacobian_multiply(a, n % N)
    if (n % 2) == 0:
        return jacobian_double(jacobian_multiply(a, n // 2))
    if (n % 2) == 1:
        return jacobian_add(jacobian_double(jacobian_multiply(a, n // 2)), a)


def to_jacobian(p):
    o = (p[0], p[1], 1)
    return o


def fast_multiply(a, n):
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))


# Curve end
code_strings = {
    2: '01',
    10: '0123456789',
    16: '0123456789abcdef',
    32: 'abcdefghijklmnopqrstuvwxyz234567',
    58: '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz',
    256: ''.join([chr(x) for x in range(256)])
}


def get_code_string(base):
    """
    Get code string for specific base encoding.

    Args:
        base (int): which base to get code string of. Valid options: 2,10,16,32,58, 256.

    Raises:
         ValueError: if an invalid base is provided.

    Returns:
        str: code string.
    """
    if base in code_strings:
        return code_strings[base]
    else:
        raise ValueError("Invalid base!")


def decode(string, base):
    """
    Decode input according to specified base.

    Args:
        string (str): input message
        base (int): base number

    Returns:
        str: decoded message.
    """
    base = int(base)
    code_string = get_code_string(base)
    result = 0
    if base == 16:
        string = string.lower()
    while len(string) > 0:
        result *= base
        result += code_string.find(str(string[0]))
        string = string[1:]
    return result


def decode_privkey(priv, formt=None):
    """
    Decode an encoded private key.

    Args:
        priv (str): private key.
        formt (str): (Optional) format identifier.

    Returns:
        str: the decoded private key.
    """
    if not formt:
        formt = get_privkey_format(priv)
    if formt == 'decimal':
        return priv
    elif formt == 'bin':
        return decode(priv, 256)
    elif formt == 'bin_compressed':
        return decode(priv[:32], 256)
    elif formt == 'hex':
        return decode(priv, 16)
    elif formt == 'hex_compressed':
        return decode(priv[:64], 16)
    elif formt == 'wif':
        return decode(b58check_to_bin(priv), 256)
    elif formt == 'wif_compressed':
        return decode(b58check_to_bin(priv)[:32], 256)
    else:
        raise Exception("WIF does not represent privkey")


def get_privkey_format(priv):
    """
    Get the private key format identifier.

    Args:
        priv (str): private key.

    Raises:
        Exception: if input does not match a known format identifier.

    Returns:
        str: format identifier.
    """
    if isinstance(priv, long):
        return 'decimal'
    elif len(priv) == 32:
        return 'bin'
    elif len(priv) == 33:
        return 'bin_compressed'
    elif len(priv) == 64:
        return 'hex'
    elif len(priv) == 66:
        return 'hex_compressed'
    else:
        bin_p = b58check_to_bin(priv)
        if len(bin_p) == 32:
            return 'wif'
        elif len(bin_p) == 33:
            return 'wif_compressed'
        else:
            raise Exception("WIF does not represent privkey")


def encode_privkey(priv, formt, vbyte=0):
    """
    Encode a private key.

    Args:
        priv (str): private key.
        formt (str): format identifier.
        vbyte:

    Raises:
        Exception: if an invalid format identifier is specified.

    Returns:
        str: key encoded according to the format identifier.
    """
    if not isinstance(priv, long):
        return encode_privkey(decode_privkey(priv), formt, vbyte)
    if formt == 'decimal':
        return priv
    elif formt == 'bin':
        return encode(priv, 256, 32)
    elif formt == 'bin_compressed':
        return encode(priv, 256, 32) + b'\x01'
    elif formt == 'hex':
        return encode(priv, 16, 64)
    elif formt == 'hex_compressed':
        return encode(priv, 16, 64) + '01'
    elif formt == 'wif':
        return bin_to_b58check(encode(priv, 256, 32), 128 + int(vbyte))
    elif formt == 'wif_compressed':
        return bin_to_b58check(encode(priv, 256, 32) + b'\x01', 128 + int(vbyte))
    else:
        raise Exception("Invalid format!")


def encode(val, base, minlen=0):
    """
    Encode the value into the specified base.

    Args:
        val (string): input value.
        base (int): base encoding number.
        minlen (int): minimum return value length.

    Returns:
        str: the encoded result with the minimum specific length if specified.
    """
    base, minlen = int(base), int(minlen)
    code_string = get_code_string(base)
    result = ""
    while val > 0:
        result = code_string[val % base] + result
        val //= base
    return code_string[0] * max(minlen - len(result), 0) + result


def encode_pubkey(pub, formt):
    """
    Encode a public key according to the format.

    Args:
        pub (tuple/list): result of self.from_jacobian()  (2 ints).
        formt (str): the format identifier.

    Returns:
        str: the encoded result with the minimum specific length if specified.
    """
    if not isinstance(pub, (tuple, list)):
        pub = decode_pubkey(pub)
    if formt == 'decimal':
        return pub
    elif formt == 'bin':
        return b'\x04' + encode(pub[0], 256, 32) + encode(pub[1], 256, 32)
    elif formt == 'bin_compressed':
        return from_int_to_byte(2 + (pub[1] % 2)) + encode(pub[0], 256, 32)
    elif formt == 'hex':
        return '04' + encode(pub[0], 16, 64) + encode(pub[1], 16, 64)
    elif formt == 'hex_compressed':
        return '0' + str(2 + (pub[1] % 2)) + encode(pub[0], 16, 64)
    elif formt == 'bin_electrum':
        return encode(pub[0], 256, 32) + encode(pub[1], 256, 32)
    elif formt == 'hex_electrum':
        return encode(pub[0], 16, 64) + encode(pub[1], 16, 64)
    else:
        raise Exception("Invalid format!")


def privkey_to_pubkey(privkey):
    """
    Get the public key associated with a private key.

    Args:
        privkey (str): private key.

    Returns:
        str:
    """
    f = get_privkey_format(privkey)
    privkey = decode_privkey(privkey, f)
    if privkey >= N:
        raise Exception("Invalid privkey")
    return encode_pubkey(fast_multiply(G, privkey), 'hex_compressed')


def from_int_to_byte(a):
    return a


def bin_to_b58check(inp, magicbyte=0):
    """
    Base58check encode the input.

    Args:
        inp (bytes): data to encode.
        magicbyte: Fixed to 0x17

    Returns:
        str: b58check encoded string.
    """
    mb = b'\x17'
    inp_fmtd = mb + inp
    #    inp_fmtd = chr(magicbyte) + inp
    checksum = bin_dbl_sha256(inp_fmtd)[:4]
    return changebase(inp_fmtd + checksum, 256, 58)


def changebase(string, frm, to, minlen=0):
    """
    Change base encodings of the input string.

    Args:
        string (str): input
        frm (int): base to change from.
        to (int): base to change to.
        minlen (int): minimum return value length.

    Returns:
        str:
    """
    if frm == to:
        return lpad(string, get_code_string(frm)[0], minlen)
    return encode(decode(string, frm), to, minlen)


def bin_dbl_sha256(s):
    """
    Perform a double SHA256 operation on the input.

    Args:
        s(str): message to hash.

    Returns:
        bytes: hash.
    """
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()


def random_string(x):
    """
    Generate a random string.

    Args:
        x(int): expected length of returned string.

    Returns:
        str:
    """
    return str(os.urandom(x))


def bytes_to_hex_string(b):
    """
    Convert bytes to hex string.

    Args:
        b (bytes): input data.

    Returns:
        str: hex string.
    """
    if isinstance(b, str):
        return b
    return ''.join('{:02x}'.format(y) for y in b)


def bin_hash160Bytes(bts):
    """
    Get a hash of the provided message using the ripemd160 algorithm.

    Args:
        bts (str): message to hash.

    Returns:
        bytes: hash.
    """
    intermed = hashlib.sha256(bts).digest()
    return hashlib.new('ripemd160', intermed).digest()


def bin_hash160(string):
    """
    Get a hash of the provided message using the ripemd160 algorithm.

    Args:
        string (str): message to hash.

    Returns:
        str: hash as a double digit hex string.
    """
    intermed = hashlib.sha256(string).digest()
    return hashlib.new('ripemd160', intermed).hexdigest()


def bin_sha256(string):
    """
    Hash the input data with the SHA256 algorithm.

    Args:
        string (bytes/str): input data.

    Returns:
        bytes: hash.
    """
    binary_data = string if type(string) is bytes else string.encode('utf-8')
    return hashlib.sha256(binary_data).digest()


def sha256(string):
    """
    Hash the input data with the SHA256 algorithm.

    Args:
        string (bytes/str): input data.

    Returns:
        str: hex string.
    """
    return bytes_to_hex_string(bin_sha256(string))


def random_key():
    """
    Generate a random 32 byte key.

    Returns:
        str: the key.
    """
    entropy = random_string(32) + str(random.randrange(2 ** 256)) + str(int(time.time() * 1000000))
    return sha256(entropy)


def base256_encode(n, minwidth=0):  # int/long to byte array
    """
    Encode the input with base256.

    Args:
        n (int): input value.
        minwidth: minimum return value length.

    Raises:
        ValueError: if a negative number is provided.

    Returns:
        bytearray:
    """
    if n > 0:
        arr = []
        while n:
            n, rem = divmod(n, 256)
            arr.append(rem)
        b = bytearray(reversed(arr))
    elif n == 0:
        b = bytearray(b'\x00')
    else:
        raise ValueError("Negative numbers not supported")

    if minwidth > 0 and len(b) < minwidth:  # zero padding needed?
        b = (minwidth - len(b)) * '\x00' + b
    b.reverse()

    return b


def xor_bytes(a, b):
    """
    XOR on two bytes objects

    Args:
        a (bytes): object 1
        b (bytes): object 2

    Returns:
        bytes: The XOR result
    """
    assert isinstance(a, bytes)
    assert isinstance(b, bytes)
    assert len(a) == len(b)
    res = bytearray()
    for i in range(len(a)):
        res.append(a[i] ^ b[i])
    return bytes(res)
