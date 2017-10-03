from boa.code.builtins import range

def Main():

    items = [ 0, 1, 2 ]

    items2 = [5,6]
    items3 = [1,2,4,5]
    count = 0

    q = 20
    for i in items:

        count += i


        if count < 20:

            for j in items2:
                count += j

                if q == 21:
                    break

                count = count + 1

                for blah in items3:
                    count = count + blah

    return count


