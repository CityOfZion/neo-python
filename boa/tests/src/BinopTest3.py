from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'5cc56b6c766b00527ac46c766b51527ac46c766b52527ac46c766b53527ac4616c766b00c36c766b51c3846c766b54527ac46c766b52c36c766b53c3966c766b55527ac46c766b00c36c766b52c3946c766b56527ac46c766b56c36c766b54c3956c766b57527ac46c766b55c36c766b53c3976c766b58527ac46c766b57c36c766b52c3866c766b59527ac46c766b54c36c766b55c3936c766b56c3936c766b57c3936c766b59c3936c766b5a527ac46c766b5ac36c766b5b527ac46203006c766b5bc3616c7566'

#note bitwise << and >> are not working...

class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b, c, d):

        j = a & b

        e = c / d

        f = a - c

        g = f * j

        k = e % d

        l = g ^ c

        m = j + e + f + g + l

        return m

