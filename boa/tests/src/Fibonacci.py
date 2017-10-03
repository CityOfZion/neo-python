
def Main(fibnumber):


    fibresult = fib(fibnumber)

    return fibresult


def fib(n):

    if n == 1 or n == 2:
        return 1

    n1 = n - 1
    n2 = n - 2

    fibr1 = fib(n1)
    fibr2 = fib(n2)

    res = fibr1 + fibr2

    return res
