from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'5bc56b6c766b00527ac46c766b51527ac46c766b52527ac46c766b53527ac4616c766b51c36c766b53c3956c766b54527ac46c766b53c36c766b52c3966c766b55527ac46c766b00c36c766b54c3936c766b56527ac46c766b56c36c766b55c3936c766b57527ac46c766b57c36c766b56c3946c766b58527ac46c766b58c36c766b55c3976c766b59527ac46c766b59c36c766b5a527ac46203006c766b5ac3616c7566'


class SCTest(FunctionCode):


    @staticmethod
    def Main(a, b, c, d):

        f = b * d

        g = d / c

        q = a + f

        m = q + g

        h = m - q

        j = h % g

        return j

