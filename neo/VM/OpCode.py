#  Constants
PUSH0 = b'\x00'  # An empty array of bytes is pushed onto the stack.
PUSHF = PUSH0
PUSHBYTES1 = b'\x01'  # b'\x01-b'\x4B The next opcode bytes is data to be pushed onto the stack
PUSHBYTES2 = b'\x02'
PUSHBYTES3 = b'\x03'
PUSHBYTES4 = b'\x04'
PUSHBYTES5 = b'\x05'
PUSHBYTES6 = b'\x06'
PUSHBYTES7 = b'\x07'
PUSHBYTES8 = b'\x08'
PUSHBYTES9 = b'\x09'
PUSHBYTES10 = b'\x0A'
PUSHBYTES11 = b'\x0B'
PUSHBYTES12 = b'\x0C'
PUSHBYTES13 = b'\x0D'
PUSHBYTES14 = b'\x0E'
PUSHBYTES15 = b'\x0F'
PUSHBYTES16 = b'\x10'
PUSHBYTES17 = b'\x11'
PUSHBYTES18 = b'\x12'
PUSHBYTES19 = b'\x13'
PUSHBYTES20 = b'\x14'
PUSHBYTES21 = b'\x15'
PUSHBYTES22 = b'\x16'
PUSHBYTES23 = b'\x17'
PUSHBYTES24 = b'\x18'
PUSHBYTES25 = b'\x19'
PUSHBYTES26 = b'\x1A'
PUSHBYTES27 = b'\x1B'
PUSHBYTES28 = b'\x1C'
PUSHBYTES29 = b'\x1D'
PUSHBYTES30 = b'\x1E'
PUSHBYTES31 = b'\x1F'
PUSHBYTES32 = b'\x20'
PUSHBYTES33 = b'\x21'
PUSHBYTES34 = b'\x22'
PUSHBYTES35 = b'\x23'
PUSHBYTES36 = b'\x24'
PUSHBYTES37 = b'\x25'
PUSHBYTES38 = b'\x26'
PUSHBYTES39 = b'\x27'
PUSHBYTES40 = b'\x28'
PUSHBYTES41 = b'\x29'
PUSHBYTES42 = b'\x2A'
PUSHBYTES43 = b'\x2B'
PUSHBYTES44 = b'\x2C'
PUSHBYTES45 = b'\x2D'
PUSHBYTES46 = b'\x2E'
PUSHBYTES47 = b'\x2F'
PUSHBYTES48 = b'\x30'
PUSHBYTES49 = b'\x31'
PUSHBYTES50 = b'\x32'
PUSHBYTES51 = b'\x33'
PUSHBYTES52 = b'\x34'
PUSHBYTES53 = b'\x35'
PUSHBYTES54 = b'\x36'
PUSHBYTES55 = b'\x37'
PUSHBYTES56 = b'\x38'
PUSHBYTES57 = b'\x39'
PUSHBYTES58 = b'\x3A'
PUSHBYTES59 = b'\x3B'
PUSHBYTES60 = b'\x3C'
PUSHBYTES61 = b'\x3D'
PUSHBYTES62 = b'\x3E'
PUSHBYTES63 = b'\x3F'
PUSHBYTES64 = b'\x40'
PUSHBYTES65 = b'\x41'
PUSHBYTES66 = b'\x42'
PUSHBYTES67 = b'\x43'
PUSHBYTES68 = b'\x44'
PUSHBYTES69 = b'\x45'
PUSHBYTES70 = b'\x46'
PUSHBYTES71 = b'\x47'
PUSHBYTES72 = b'\x48'
PUSHBYTES73 = b'\x49'
PUSHBYTES74 = b'\x4A'
PUSHBYTES75 = b'\x4B'
PUSHDATA1 = b'\x4C'  # The next byte contains the number of bytes to be pushed onto the stack.
PUSHDATA2 = b'\x4D'  # The next two bytes contain the number of bytes to be pushed onto the stack.
PUSHDATA4 = b'\x4E'  # The next four bytes contain the number of bytes to be pushed onto the stack.
PUSHM1 = b'\x4F'  # The number -1 is pushed onto the stack.
PUSH1 = b'\x51'  # The number 1 is pushed onto the stack.
PUSHT = PUSH1
PUSH2 = b'\x52'  # The number 2 is pushed onto the stack.
PUSH3 = b'\x53'  # The number 3 is pushed onto the stack.
PUSH4 = b'\x54'  # The number 4 is pushed onto the stack.
PUSH5 = b'\x55'  # The number 5 is pushed onto the stack.
PUSH6 = b'\x56'  # The number 6 is pushed onto the stack.
PUSH7 = b'\x57'  # The number 7 is pushed onto the stack.
PUSH8 = b'\x58'  # The number 8 is pushed onto the stack.
PUSH9 = b'\x59'  # The number 9 is pushed onto the stack.
PUSH10 = b'\x5A'  # The number 10 is pushed onto the stack.
PUSH11 = b'\x5B'  # The number 11 is pushed onto the stack.
PUSH12 = b'\x5C'  # The number 12 is pushed onto the stack.
PUSH13 = b'\x5D'  # The number 13 is pushed onto the stack.
PUSH14 = b'\x5E'  # The number 14 is pushed onto the stack.
PUSH15 = b'\x5F'  # The number 15 is pushed onto the stack.
PUSH16 = b'\x60'  # The number 16 is pushed onto the stack.


#  Flow control
NOP = b'\x61'  # Does nothing.
JMP = b'\x62'
JMPIF = b'\x63'
JMPIFNOT = b'\x64'
CALL = b'\x65'
RET = b'\x66'
APPCALL = b'\x67'
SYSCALL = b'\x68'
TAILCALL = b'\x69'


# Exceptions
THROW = b'\xf0'
THROWIFNOT = b'\xf1'


#  Stack
DUPFROMALTSTACK = b'\x6A'
TOALTSTACK = b'\x6B'  # Puts the input onto the top of the alt stack. Removes it from the main stack.
FROMALTSTACK = b'\x6C'  # Puts the input onto the top of the main stack. Removes it from the alt stack.
XDROP = b'\x6D'
XSWAP = b'\x72'
XTUCK = b'\x73'
DEPTH = b'\x74'  # Puts the number of stack items onto the stack.
DROP = b'\x75'  # Removes the top stack item.
DUP = b'\x76'  # Duplicates the top stack item.
NIP = b'\x77'  # Removes the second-to-top stack item.
OVER = b'\x78'  # Copies the second-to-top stack item to the top.
PICK = b'\x79'  # The item n back in the stack is copied to the top.
ROLL = b'\x7A'  # The item n back in the stack is moved to the top.
ROT = b'\x7B'  # The top three items on the stack are rotated to the left.
SWAP = b'\x7C'  # The top two items on the stack are swapped.
TUCK = b'\x7D'  # The item at the top of the stack is copied and inserted before the second-to-top item.


#  Splice
CAT = b'\x7E'  # Concatenates two strings.
SUBSTR = b'\x7F'  # Returns a section of a string.
LEFT = b'\x80'  # Keeps only characters left of the specified point in a string.
RIGHT = b'\x81'  # Keeps only characters right of the specified point in a string.
SIZE = b'\x82'  # Returns the length of the input string.


#  Bitwise logic
INVERT = b'\x83'  # Flips all of the bits in the input.
AND = b'\x84'  # Boolean and between each bit in the inputs.
OR = b'\x85'  # Boolean or between each bit in the inputs.
XOR = b'\x86'  # Boolean exclusive or between each bit in the inputs.
EQUAL = b'\x87'  # Returns 1 if the inputs are exactly equal' 0 otherwise.
# OP_EQUALVERIFY = b'\x88' #  Same as OP_EQUAL' but runs OP_VERIFY afterward.
# OP_RESERVED1 = b'\x89' #  Transaction is invalid unless occuring in an unexecuted OP_IF branch
# OP_RESERVED2 = b'\x8A' #  Transaction is invalid unless occuring in an unexecuted OP_IF branch

#  Arithmetic
#  Note: Arithmetic inputs are limited to signed 32-bit integers' but may overflow their output.
INC = b'\x8B'  # 1 is added to the input.
DEC = b'\x8C'  # 1 is subtracted from the input.
SIGN = b'\x8D'
NEGATE = b'\x8F'  # The sign of the input is flipped.
ABS = b'\x90'  # The input is made positive.
NOT = b'\x91'  # If the input is 0 or 1' it is flipped. Otherwise the output will be 0.
NZ = b'\x92'  # Returns 0 if the input is 0. 1 otherwise.
ADD = b'\x93'  # a is added to b.
SUB = b'\x94'  # b is subtracted from a.
MUL = b'\x95'  # a is multiplied by b.
DIV = b'\x96'  # a is divided by b.
MOD = b'\x97'  # Returns the remainder after dividing a by b.
SHL = b'\x98'  # Shifts a left b bits' preserving sign.
SHR = b'\x99'  # Shifts a right b bits' preserving sign.
BOOLAND = b'\x9A'  # If both a and b are not 0' the output is 1. Otherwise 0.
BOOLOR = b'\x9B'  # If a or b is not 0' the output is 1. Otherwise 0.
NUMEQUAL = b'\x9C'  # Returns 1 if the numbers are equal' 0 otherwise.
NUMNOTEQUAL = b'\x9E'  # Returns 1 if the numbers are not equal' 0 otherwise.
LT = b'\x9F'  # Returns 1 if a is less than b' 0 otherwise.
GT = b'\xA0'  # Returns 1 if a is greater than b' 0 otherwise.
LTE = b'\xA1'  # Returns 1 if a is less than or equal to b' 0 otherwise.
GTE = b'\xA2'  # Returns 1 if a is greater than or equal to b' 0 otherwise.
MIN = b'\xA3'  # Returns the smaller of a and b.
MAX = b'\xA4'  # Returns the larger of a and b.
WITHIN = b'\xA5'  # Returns 1 if x is within the specified range (left-inclusive)' 0 otherwise.

#  Crypto
# RIPEMD160 = b'\xA6' #  The input is hashed using RIPEMD-160.
SHA1 = b'\xA7'  # The input is hashed using SHA-1.
SHA256 = b'\xA8'  # The input is hashed using SHA-256.
HASH160 = b'\xA9'
HASH256 = b'\xAA'
CHECKSIG = b'\xAC'
CHECKMULTISIG = b'\xAE'


#  Array
ARRAYSIZE = b'\xC0'
PACK = b'\xC1'
UNPACK = b'\xC2'
PICKITEM = b'\xC3'
SETITEM = b'\xC4'
NEWARRAY = b'\xC5'  # 用作引用類型
NEWSTRUCT = b'\xC6'  # 用作值類型
APPEND = b'\xC8'
REVERSE = b'\xC9'
REMOVE = b'\xCA'

DEBUG = b'\xCD'

import sys
import importlib
import binascii

module = importlib.import_module('neo.VM.OpCode')
items = dir(sys.modules[__name__])


def ToName(op):

    if type(op) is bytes:
        op = int.from_bytes(op, 'little')

    for item in items:
        n = getattr(module, item)

        try:
            nn = int(binascii.hexlify(n), 16)

            if op == nn:
                return item
        except Exception as e:
            pass

        try:
            nn2 = int.from_bytes(n, 'little')
            if op == nn2:
                return item
        except Exception as e:
            pass

    return None
