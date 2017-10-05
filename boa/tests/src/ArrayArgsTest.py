from boa.blockchain.vm.Neo.Runtime import Log
from boa.code.builtins import concat

def Main( operation, items):

    j = 10

    if operation == 'dostuff':

        j = 3

        if len(items) == 2:


            bytes1 = items[0]
            bytes2 = items[1]


            len1 = len(bytes1)
            len2 = len(bytes2)

            total = concat(bytes1,bytes2)

#            j = len1 + len2

            if total == 137707327489:
                Log("awesome!")

            else:
                Log("bad")


        else:

            j = 23


    elif operation == 'dont':

        j = 4


    return j
