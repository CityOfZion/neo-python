
from neo.Cryptography.ECCurve import ECDSA,FiniteField
from neo.Cryptography.Helper import *
import random

prikey = bin_hash160('city of zion'.encode('utf-8'))
#print("prikey : %s " % prikey)

curve = ECDSA.secp256r1()

point = curve.calcpub(prikey)

#print("pubkey %s %s" % (point.x, point.y))

coz = ['canesin', 'afong' ,'ashant', 'unigorant', 'fabwa', 'lllwvlvwlll', 'totalvamp', 'luciano_engel', 'localhuman',]

sorted(coz)

#print("coz: %s " % coz)

str = ' '.join(coz).encode('utf-8')

message = bin_hash160( str )


#print("message: %s " % message)
px,py = curve.sign( message, prikey, 10000000 )

#print("script: %s  %s" % (px, py))


letters = [point.x, point.y, px, py]
newletters = []
for l in letters:
#    print("letter: %s %s " % (type(l), l))
    hx = hex(l.value)
#    print("hex: %s " % hx)
    newletters.append(hx)
    ba = bytearray(binascii.unhexlify(hx[2:]))
#    print("ba: %s " % ba)
#    print("ba: %s " % ba)
    newletters.append([chr(b) for b in ba])
    newletters.append([b for b in ba])

#print("letters: %s " % letters)
#print("new letters: %s " % newletters)

f = [p.value for p in letters] + newletters + ['            ', '    ', '                                        ',
                                               '                                ',  '   ',
                                               '                                                                                                ',
                                               '                                                                                                                                                                                                ',
                                               '    ',]
f *= 100
random.shuffle(f)
print("f: %s " % f)

