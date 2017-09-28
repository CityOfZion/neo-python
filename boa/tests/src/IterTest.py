from boa.code.builtins import range
def Main():


    range_list = range(1,2)


    count = 0

    for i in range_list:

        count = count + i

    a = awesome()

    return count + a


def awesome():

    return 2
