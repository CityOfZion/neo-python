def Main(a, b):

    j = 0

    if a > b:

        j = a

    else:

        j = b

    return j

import dis

from dis import disassemble
dis.dis(Main)

import di