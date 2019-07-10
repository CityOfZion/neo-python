# -*- coding:utf-8 -*-
"""
Description:
    ECC Curve
Usage:
    from neo.Core.Cryptography.ECCurve import ECCurve
"""
import random
import binascii
from mpmath.libmp import bitcount as _bitlength

modpow = pow


# (gcd,c,d)= GCD(a, b)  ===> a*c+b*d!=gcd:


def GCD(a, b):
    if (a == 0):
        return (b, 0, 1)
    d1, x1, y1 = GCD(b % a, a)
    return (d1, y1 - (b // a) * x1, x1)


def modinv(x, m):
    (gcd, c, d) = GCD(x, m)
    return c


def samefield(a, b):
    """
    determine if a uses the same field
    """
    if a.field != b.field:
        return False
    return True


def test_bit(num, index):
    if (num & (1 << index)):
        return True
    return False


def randbytes(n):
    for i in range(0, n):
        yield random.getrandbits(8)


def next_random_integer(size_in_bits):
    """
    Args:
        size_in_bits (int): used to specify the size in bits of the random integer

    Returns:
        int: random integer

    Raises:
        ValueError: if the specified size in bits is < 0
    """
    if size_in_bits < 0:
        raise ValueError(f'size in bits ({size_in_bits}) must be greater than zero')
    if size_in_bits == 0:
        return 0

    balen = int(size_in_bits / 8) + 1
    ba = bytearray(randbytes(balen))

    if size_in_bits % 8 == 0:
        ba[balen - 1] = 0
    else:
        ba[balen - 1] &= (1 << size_in_bits % 8) - 1
    return int.from_bytes(ba, 'big')


def _lucas_sequence(n, P, Q, k):
    """
    Returns:
        The modular Lucas sequence (U_k, V_k, Q_k).
        Given a Lucas sequence defined by P, Q, returns the kth values for
        U and V, along with Q^k, all modulo n.

    Raises:
        ValueError:
            if n is < 2
            if k < 0
            if D == 0
    """
    D = P * P - 4 * Q
    if n < 2:
        raise ValueError("n must be >= 2")
    if k < 0:
        raise ValueError("k must be >= 0")
    if D == 0:
        raise ValueError("D must not be zero")

    if k == 0:
        return 0, 2
    U = 1
    V = P
    Qk = Q
    b = _bitlength(k)
    if Q == 1:
        # For strong tests
        while b > 1:
            U = (U * V) % n
            V = (V * V - 2) % n
            b -= 1
            if (k >> (b - 1)) & 1:
                t = U * D
                U = U * P + V
                if U & 1:
                    U += n
                U >>= 1
                V = V * P + t
                if V & 1:
                    V += n
                V >>= 1
    elif P == 1 and Q == -1:
        # For Selfridge parameters
        while b > 1:
            U = (U * V) % n
            if Qk == 1:
                V = (V * V - 2) % n
            else:
                V = (V * V + 2) % n
                Qk = 1
            b -= 1
            if (k >> (b - 1)) & 1:
                t = U * D
                U = U + V
                if U & 1:
                    U += n
                U >>= 1
                V = V + t
                if V & 1:
                    V += n
                V >>= 1
                Qk = -1
    else:
        # The general case with any P and Q
        while b > 1:
            U = (U * V) % n
            V = (V * V - 2 * Qk) % n
            Qk *= Qk
            b -= 1
            if (k >> (b - 1)) & 1:
                t = U * D
                U = U * P + V
                if U & 1:
                    U += n
                U >>= 1
                V = V * P + t
                if V & 1:
                    V += n
                V >>= 1
                Qk *= Q
            Qk %= n
    U %= n
    V %= n
    return U, V


def sqrtCQ(val, CQ):
    """
    Raises:
        LegendaireExponentError: if modpow(val, legendreExponent, CQ) != 1
    """
    if test_bit(CQ, 1):
        z = modpow(val, (CQ >> 2) + 1, CQ)
        zsquare = (z * z) % CQ
        if zsquare == val:
            return z
        else:
            return None

    qMinusOne = CQ - 1
    legendreExponent = qMinusOne >> 1
    if modpow(val, legendreExponent, CQ) != 1:
        raise LegendaireExponentError()

    u = qMinusOne >> 2
    k = (u << 1) + 1
    Q = val
    fourQ = (Q << 2) % CQ
    U = None
    V = None

    while U == 1 or U == qMinusOne:

        P = next_random_integer(CQ.bit_length())
        while P >= CQ or modpow(P * P - fourQ, legendreExponent, CQ) != qMinusOne:
            P = next_random_integer(CQ.bit_length())

        U, V = _lucas_sequence(CQ, P, Q, k)
        if (V * V) % CQ == fourQ:

            if test_bit(V, 0):
                V += CQ

            V >>= 1
            assert (V * V) % CQ == val
            return V

    return None


class LegendaireExponentError(Exception):
    """Provide user friendly feedback in case of a legendaire exponent error."""
    pass


class FiniteField:
    """
    FiniteField implements a value modulus a number.
    """

    class Value:
        """
        represent a value in the FiniteField
        this class forwards all operations to the FiniteField class
        """

        def __init__(self, field, value):
            self.field = field
            self.value = field.integer(value)

        # Value * int
        def __add__(self, rhs):
            return self.field.add(self, self.field.value(rhs))

        def __sub__(self, rhs):
            return self.field.sub(self, self.field.value(rhs))

        def __mul__(self, rhs):
            return self.field.mul(self, self.field.value(rhs))

        def __truediv__(self, rhs):
            return self.field.div(self, self.field.value(rhs))

        def __pow__(self, rhs):
            return self.field.pow(self, rhs)

        # int * Value
        def __radd__(self, rhs):
            return self.field.add(self.field.value(rhs), self)

        def __rsub__(self, rhs):
            return self.field.sub(self.field.value(rhs), self)

        def __rmul__(self, rhs):
            return self.field.mul(self.field.value(rhs), self)

        def __rdiv__(self, rhs):
            return self.field.div(self.field.value(rhs), self)

        def __rpow__(self, rhs):
            return self.field.pow(self.field.value(rhs), self)

        def __eq__(self, rhs):
            return self.field.eq(self, self.field.value(rhs))

        def __ne__(self, rhs):
            return not (self == rhs)

        def __str__(self):
            return "0x%s" % self.value

        def __neg__(self):
            return self.field.neg(self)

        def sqrt(self, flag):
            return self.field.sqrt(self, flag)

        def sqrtCQ(self, CQ):
            try:
                res = self.field.sqrtCQ(self, CQ)
            except LegendaireExponentError:
                res = None
            return res

        def inverse(self):
            return self.field.inverse(self)

        def iszero(self):
            return self.value == 0

    def __init__(self, p):
        self.p = p

    """
    several basic operators
    """

    def add(self, lhs, rhs):
        return samefield(lhs, rhs) and self.value((lhs.value + rhs.value) % self.p)

    def sub(self, lhs, rhs):
        return samefield(lhs, rhs) and self.value((lhs.value - rhs.value) % self.p)

    def mul(self, lhs, rhs):
        return samefield(lhs, rhs) and self.value((lhs.value * rhs.value) % self.p)

    def div(self, lhs, rhs):
        return samefield(lhs, rhs) and self.value((lhs.value * rhs.inverse()) % self.p)

    def pow(self, lhs, rhs):
        return self.value(pow(int(lhs.value), int(self.integer(rhs)), self.p))

    def eq(self, lhs, rhs):
        return (lhs.value - rhs.value) % self.p == 0

    def neg(self, val):
        return self.value(self.p - val.value)

    def sqrt(self, val, flag):
        """
        calculate the square root modulus p

        Raises:
            ValueError: if self.p % 8 == 1
        """
        if val.iszero():
            return val
        sw = self.p % 8
        if sw == 3 or sw == 7:
            res = val ** ((self.p + 1) / 4)
        elif sw == 5:
            x = val ** ((self.p + 1) / 4)
            if x == 1:
                res = val ** ((self.p + 3) / 8)
            else:
                res = (4 * val) ** ((self.p - 5) / 8) * 2 * val
        else:
            raise ValueError("modsqrt non supported for (p%8)==1")

        if res.value % 2 == flag:
            return res
        else:
            return -res

    def inverse(self, value):
        """
        calculate the multiplicative inverse
        """
        return modinv(value.value, self.p)

    def value(self, x):
        """
        converts an integer or FinitField.Value to a value of this FiniteField.
        """
        return x if isinstance(x, FiniteField.Value) and x.field == self else FiniteField.Value(self, x)

    def integer(self, x):
        """
        returns a plain integer
        """
        if type(x) is str:
            hex = binascii.unhexlify(x)
            return int.from_bytes(hex, 'big')

        return x.value if isinstance(x, FiniteField.Value) else x

    def zero(self):
        """
        returns the additive identity value
        meaning:  a + 0 = a
        """
        return FiniteField.Value(self, 0)

    def one(self):
        """
        returns the multiplicative identity value
        meaning a * 1 = a
        """
        return FiniteField.Value(self, 1)


class EllipticCurve:
    """
    EllipticCurve implements a point on a elliptic curve
    """

    class ECPoint:
        """
        represent a value in the EllipticCurve
        this class forwards all operations to the EllipticCurve class
        """

        def __init__(self, curve, x, y):
            self.curve = curve
            self.x = x
            self.y = y

        # Point + Point

        def __add__(self, rhs):
            return self.curve.add(self, rhs)

        def __sub__(self, rhs):
            return self.curve.sub(self, rhs)

        # Point * int   or Point * Value
        def __mul__(self, rhs):
            return self.curve.mul(self, rhs)

        def __truediv__(self, rhs):
            return self.curve.div(self, rhs)

        def __eq__(self, rhs):
            return self.curve.eq(self, rhs)

        def __ne__(self, rhs):
            return not (self == rhs)

        def __lt__(self, other):
            if other == self:
                return False
            elif self.x.value < other.x.value:
                return True
            elif self.x.value > other.x.value:
                return False
            elif self.x.value == other.x.value:
                return False

            return self.y.value < other.y.value

        def __gt__(self, other):
            if other == self:
                return False
            elif self.x.value > other.x.value:
                return True
            elif self.x.value < other.x.value:
                return False
            elif self.x.value == other.x.value:
                return False

            return self.y.value > other.y.value

        def __le__(self, other):
            if other == self:
                return True
            return self.__lt__(other)

        def __ge__(self, other):
            if other == self:
                return True
            return self.__gt__(other)

        def __str__(self):
            return "(%s,%s)" % (self.x, self.y)

        def __neg__(self):
            return self.curve.neg(self)

        def iszero(self):
            return self.x.iszero() and self.y.iszero()

        def isoncurve(self):
            return self.curve.isoncurve(self)

        @property
        def IsInfinity(self):
            return True if self == self.curve.Infinity else False

        def Size(self):
            if self.IsInfinity:
                return 1
            else:
                return 33

        def encode_point(self, compressed=True, endian='little'):

            if self.IsInfinity:
                return bytearray([0])

            xbytes = bytearray(self.x.value.to_bytes(32, endian))
            xbytes.reverse()

            if compressed:
                byteone = b'\x03'
                if self.y.value % 2 == 0:
                    byteone = b'\x02'

                data = bytearray(byteone) + xbytes
                return binascii.hexlify(data)

            else:

                ybytes = bytearray(self.y.value.to_bytes(32, endian))
                ybytes.reverse()

                data = bytearray(b'\x04') + xbytes + ybytes
                return binascii.hexlify(data)

        def ToString(self):
            return binascii.hexlify(self.encode_point(compressed=True)).decode('utf-8')

        def ToBytes(self):
            return binascii.hexlify(self.encode_point(compressed=True))

        def Serialize(self, writer, compress=True):
            if self == self.curve.Infinity:
                writer.WriteByte(b'\x00')
            else:
                byt = self.encode_point(compressed=compress)
                writer.WriteBytes(byt)

    def __init__(self, field, a, b):
        self.field = field
        self.a = field.value(a)
        self.b = field.value(b)

    @property
    def Infinity(self):
        return self.point(0, 0)

    def add(self, p, q):
        """
        perform elliptic curve addition
        """
        if p.iszero():
            return q
        if q.iszero():
            return p

        lft = 0
        # calculate the slope of the intersection line
        if p == q:
            if p.y == 0:
                return self.zero()
            lft = (3 * p.x ** 2 + self.a) / (2 * p.y)
        elif p.x == q.x:
            return self.zero()
        else:
            lft = (p.y - q.y) / (p.x - q.x)

        # calculate the intersection point
        x = lft ** 2 - (p.x + q.x)
        y = lft * (p.x - x) - p.y
        return self.point(x, y)

    # subtraction is :  a - b  =  a + -b
    def sub(self, lhs, rhs):
        return lhs + -rhs

    # scalar multiplication is implemented like repeated addition
    def mul(self, pt, scalar):
        scalar = self.field.integer(scalar)
        accumulator = self.zero()
        shifter = pt

        while scalar != 0:
            bit = scalar % 2
            if bit:
                accumulator += shifter
            shifter += shifter
            scalar /= 2

        return accumulator

    def div(self, pt, scalar):
        """
        scalar division:  P / a = P * (1/a)
        scalar is assumed to be of type FiniteField(grouporder)
        """
        return pt * (1 / scalar)

    def eq(self, lhs, rhs):
        return lhs.x == rhs.x and lhs.y == rhs.y

    def neg(self, pt):
        return self.point(pt.x, -pt.y)

    def zero(self):
        """
        Return the additive identity point ( aka '0' )
        P + 0 = P
        """
        return self.point(self.field.zero(), self.field.zero())

    def point(self, x, y):
        """
        construct a point from 2 values
        """
        return EllipticCurve.ECPoint(self, self.field.value(x), self.field.value(y))

    def isoncurve(self, p):
        """
        verifies if a point is on the curve
        """
        return p.iszero() or p.y ** 2 == p.x ** 3 + self.a * p.x + self.b

    def decompress(self, x, flag):
        """
        calculate the y coordinate given only the x value.
        there are 2 possible solutions, use 'flag' to select.
        """
        x = self.field.value(x)
        ysquare = x ** 3 + self.a * x + self.b

        return self.point(x, ysquare.sqrt(flag))

    def decode_from_reader(self, reader):
        """
        Raises:
            NotImplementedError: if an unsupported point encoding is used
            TypeError: if unexpected encoding is read
        """
        try:
            f = reader.ReadByte()
        except ValueError:
            return self.Infinity

        f = int.from_bytes(f, "little")
        if f == 0:
            return self.Infinity

        # these are compressed
        if f == 2 or f == 3:
            yTilde = f & 1
            data = bytearray(reader.ReadBytes(32))
            data.reverse()
            data.append(0)
            X1 = int.from_bytes(data, 'little')
            return self.decompress_from_curve(X1, yTilde)

        # uncompressed or hybrid
        elif f == 4 or f == 6 or f == 7:
            raise NotImplementedError()

        raise ValueError(f"Invalid point encoding: {f}")

    def decode_from_hex(self, hex_str, unhex=True):
        """
        Raises:
            ValueError: if the hex_str is an incorrect length for encoding or compressed encoding
            NotImplementedError: if an unsupported point encoding is used
            TypeError: if unexpected encoding is read
        """
        ba = None
        if unhex:
            ba = bytearray(binascii.unhexlify(hex_str))
        else:
            ba = hex_str

        cq = self.field.p

        expected_byte_len = int((_bitlength(cq) + 7) / 8)

        f = ba[0]

        if f == 0:
            return self.Infinity

        # these are compressed
        if f == 2 or f == 3:
            if len(ba) != expected_byte_len + 1:
                raise ValueError("Incorrect length for encoding")
            yTilde = f & 1
            data = bytearray(ba[1:])
            data.reverse()
            data.append(0)
            X1 = int.from_bytes(data, 'little')
            return self.decompress_from_curve(X1, yTilde)

        # uncompressed or hybrid
        elif f == 4:

            if len(ba) != (2 * expected_byte_len) + 1:
                raise ValueError("Incorrect length for compressed encoding")

            x_data = bytearray(ba[1:1 + expected_byte_len])
            x_data.reverse()
            x_data.append(0)

            y_data = bytearray(ba[1 + expected_byte_len:])
            y_data.reverse()
            y_data.append(0)

            x = int.from_bytes(x_data, 'little')
            y = int.from_bytes(y_data, 'little')

            pnt = self.point(x, y)
            return pnt

        elif f == 6 or f == 7:
            raise NotImplementedError()

        else:
            raise ValueError(f"Invalid point encoding: {f}")

    def decompress_from_curve(self, x, flag):
        """
        calculate the y coordinate given only the x value.
        there are 2 possible solutions, use 'flag' to select.
        """

        cq = self.field.p
        x = self.field.value(x)

        ysquare = x ** 3 + self.a * x + self.b

        try:
            ysquare_root = sqrtCQ(ysquare.value, cq)
        except LegendaireExponentError:
            ysquare_root = None

        bit0 = 0
        if ysquare_root % 2 is not 0:
            bit0 = 1

        if bit0 != flag:
            beta = (cq - ysquare_root) % cq
        else:
            beta = ysquare_root

        return self.point(x, beta)


class ECDSA:
    """
    Digital Signature Algorithm using Elliptic Curves
    """

    def __init__(self, ec, G, n):
        self.ec = ec
        self.G = G
        self.GFn = FiniteField(n)

    @property
    def Curve(self):
        return self.ec

    def calcpub(self, privkey):
        """
        calculate the public key for private key x
        return G*x
        """
        return self.G * self.GFn.value(privkey)

    def sign(self, message, privkey, secret):
        """
        sign the message using private key and sign secret
        for signsecret k, message m, privatekey x
        return (G*k,  (m+x*r)/k)
        """
        m = self.GFn.value(message)
        x = self.GFn.value(privkey)
        k = self.GFn.value(secret)

        R = self.G * k

        r = self.GFn.value(R.x)
        s = (m + x * r) / k

        return (r, s)

    def verify(self, message, pubkey, rnum, snum):
        """
        Verify the signature
        for message m, pubkey Y, signature (r,s)
        r = xcoord(R)
        verify that :  G*m+Y*r=R*s
        this is true because: { Y=G*x, and R=G*k, s=(m+x*r)/k }

        G*m+G*x*r = G*k*(m+x*r)/k  ->
        G*(m+x*r) = G*(m+x*r)
        several ways to do the verification:
            r == xcoord[ G*(m/s) + Y*(r/s) ]  <<< the standard way
            R * s == G*m + Y*r
            r == xcoord[ (G*m + Y*r)/s) ]

        """
        m = self.GFn.value(message)
        r = self.GFn.value(rnum)
        s = self.GFn.value(snum)

        R = self.G * (m / s) + pubkey * (r / s)

        # alternative methods of verifying
        # RORG= self.ec.decompress(r, 0)
        # RR = self.G * m + pubkey * r
        # print "#1: %s .. %s"  % (RR, RORG*s)
        # print "#2: %s .. %s"  % (RR*(1/s), r)
        # print "#3: %s .. %s"  % (R, r)

        return R.x == r

    def findpk(self, message, rnum, snum, flag):
        """
        find pubkey Y from message m, signature (r,s)
        Y = (R*s-G*m)/r
        note that there are 2 pubkeys related to a signature
        """
        m = self.GFn.value(message)
        r = self.GFn.value(rnum)
        s = self.GFn.value(snum)

        R = self.ec.decompress(r, flag)

        # return (R*s - self.G * m)*(1/r)
        return R * (s / r) - self.G * (m / r)

    def findpk2(self, r1, s1, r2, s2, flag1, flag2):
        """
        find pubkey Y from 2 different signature on the same message
        sigs: (r1,s1) and (r2,s2)
        returns  (R1*s1-R2*s2)/(r1-r2)
        """
        R1 = self.ec.decompress(r1, flag1)
        R2 = self.ec.decompress(r2, flag2)

        rdiff = self.GFn.value(r1 - r2)

        return (R1 * s1 - R2 * s2) * (1 / rdiff)

    def crack2(self, r, s1, s2, m1, m2):
        """
        find signsecret and privkey from duplicate 'r'
        signature (r,s1) for message m1
        and signature (r,s2) for message m2
        s1= (m1 + x*r)/k
        s2= (m2 + x*r)/k
        subtract -> (s1-s2) = (m1-m2)/k  ->  k = (m1-m2)/(s1-s2)
        -> privkey =  (s1*k-m1)/r  .. or  (s2*k-m2)/r
        """
        sdelta = self.GFn.value(s1 - s2)
        mdelta = self.GFn.value(m1 - m2)

        secret = mdelta / sdelta
        x1 = self.crack1(r, s1, m1, secret)
        x2 = self.crack1(r, s2, m2, secret)

        if x1 != x2:
            print("x1= %s" % x1)
            print("x2= %s" % x2)

        return (secret, x1)

    def crack1(self, rnum, snum, message, signsecret):
        """
        find privkey, given signsecret k, message m, signature (r,s)
        x= (s*k-m)/r
        """
        m = self.GFn.value(message)
        r = self.GFn.value(rnum)
        s = self.GFn.value(snum)
        k = self.GFn.value(signsecret)
        return (s * k - m) / r

    @staticmethod
    def secp256r1():
        """
        create the secp256r1 curve
        """
        GFp = FiniteField(int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16))
        ec = EllipticCurve(GFp, 115792089210356248762697446949407573530086143415290314195533631308867097853948, 41058363725152142129326129780047268409114441015993725554835256314039467401291)
        # return ECDSA(GFp, ec.point(0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5),int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16))
        return ECDSA(ec,
                     ec.point(0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296, 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5),
                     GFp)

    @staticmethod
    def decode_secp256r1(str, unhex=True, check_on_curve=True):
        """
        decode a public key on the secp256r1 curve

        Raises:
            ValueError: if input `str` could not be decoded
        """

        GFp = FiniteField(int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16))
        ec = EllipticCurve(GFp, 115792089210356248762697446949407573530086143415290314195533631308867097853948,
                           41058363725152142129326129780047268409114441015993725554835256314039467401291)

        point = ec.decode_from_hex(str, unhex=unhex)

        if check_on_curve:
            if point.isoncurve():
                return ECDSA(GFp, point, int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16))
            else:
                raise ValueError(f"Could not decode string: {str}")

        return ECDSA(GFp, point, int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16))

    @staticmethod
    def Deserialize_Secp256r1(reader):
        GFp = FiniteField(int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16))
        ec = EllipticCurve(GFp, 115792089210356248762697446949407573530086143415290314195533631308867097853948,
                           41058363725152142129326129780047268409114441015993725554835256314039467401291)

        return ec.decode_from_reader(reader)

    @staticmethod
    def FromBytes_Secp256r1(pubkey):
        length = len(pubkey)

        if length == 33 or length == 65:
            return ECDSA.decode_secp256r1(pubkey)

        elif length == 64 or length == 72:
            skip = length - 64
            out = bytearray(b'04').hex() + pubkey[skip:]
            return ECDSA.decode_secp256r1(out)

        elif length == 96 or length == 104:
            skip = length - 96

            out = bytearray(b'\x04') + bytearray(pubkey[skip:skip + 64])

            return ECDSA.decode_secp256r1(out, unhex=False, check_on_curve=False)

    @staticmethod
    def secp256k1():
        """
        create the secp256k1 curve
        """
        GFp = FiniteField(2 ** 256 - 2 ** 32 - 977)  # This is P from below... aka FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        ec = EllipticCurve(GFp, 0, 7)
        return ECDSA(ec, ec.point(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8), 2 ** 256 - 432420386565659656852420866394968145599)

    @staticmethod
    def SignSecp256R1(message, prikey, pubkey):

        GFp = FiniteField(int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16))
        ec = EllipticCurve(GFp, 115792089210356248762697446949407573530086143415290314195533631308867097853948, 41058363725152142129326129780047268409114441015993725554835256314039467401291)

        edcsa = ECDSA(ec, ec.point(pubkey.x.value, pubkey.y.value), GFp)

        res = edcsa.sign(message, prikey)

        return res
