
from boa.code.builtins import range

def Main():

    a = range(100, 120)

    #b = a[4] # this will fail, since the range list is only 4 elements long ( 0, 1, 2, 3 )

    b = a[3]

    return b

