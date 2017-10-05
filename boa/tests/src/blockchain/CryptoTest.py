from boa.code.builtins import sha1,sha256, hash160,hash256
from boa.blockchain.vm.Neo.Runtime import Notify


def Main():


    a = 'snathoeu'

    asha = sha1(a)


    if asha == b'\xd1\xc4\xee\xb2[\xe9\x95\x17{\x80\x96\xd6\xe10A\xa4\x16\xd3tU':
        print("ok1")

    a2 = 'abcd'
    a2sha256 = sha256(a2)

    if a2sha256 == b'\x88\xd4&o\xd4\xe63\x8d\x13\xb8E\xfc\xf2\x89W\x9d \x9c\x89x#\xb9!}\xa3\xe1a\x93o\x03\x15\x89':
        print("ok2")


    a3 = 'zwxy'

    a3160 = hash160(a3)

    if a3160 == b'V\x9e\x8f!\x9d\xc7\x0e\xceL;\x1b\xec\xe25\x94\ty\xc2_\xf1':
        print("ok3")


    a4 = 'abcdabcdabcdabcd'

    a4h256 = hash256(a4)


    if a4h256 == b"\xafw\xab\xa2\xe9\x9c\xa2cO\x06w\x97s\xc6\xd1\x9dh\xc8*\xf4\x9c'\x95\x0f\xe9x1\xe7\xa4/\xcb\xc9":
        print("ok4")






    return 1