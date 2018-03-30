from boa.builtins import breakpoint


def Main(operation):

    result = False
    if operation == 1:

        m = 3

        breakpoint()
        result = True

    elif operation == 2:

        breakpoint()
        result = False

    elif operation == 3:
        b = 'hello'
        breakpoint()
        j = 32
        breakpoint()
        result = True

    elif operation == 4:
        n = 2
        res = another_method(n)
        result = res

    return result


def another_method(j):

    q = j + 5

    breakpoint()
    return q
