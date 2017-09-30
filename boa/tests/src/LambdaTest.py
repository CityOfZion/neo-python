

def Main():

    q = lambda x: x + 1

    m = q(3)

    j = lambda y: y * 3


    n = j(3)

    #this wont work..
    #return q(3) + j(8)

    a = awesome()

    return m + n - a



def awesome():


    c = lambda x: x + 2


    out = c(2)

    return out