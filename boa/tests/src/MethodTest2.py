
def Main():

    a = 1

    b = 2

    c = stuff()

    d = stuff2()

    e = stuff8()

    f = blah()

    h = prevcall()

    return a + c + d + f + b + h


def stuff():

    a = 4

    b = 2

    return a + b


def stuff2():

    a = 8

    j = 10

    return j - a

def prevcall():


    return stuff()

def stuff8():

    q = 'hello'

    return q


def blah():

    return 1 + 8