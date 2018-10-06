
def Main(operation):

    if operation == 'testFail':

        callBadMethod(1, 2)

        return True

    elif operation == 'testException':

        raise Exception("An exception has been raised")

    return False


def callBadMethod(a, b, c):

    return False
