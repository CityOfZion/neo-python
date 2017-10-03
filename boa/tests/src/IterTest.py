from boa.code.builtins import range

def Main():

    count = 0

    for i in range(0,5):
        count = count + i
        count += awesome()
        count += not_so_awesome()

    return count

def awesome():

    return 2

def not_so_awesome():
    return -1