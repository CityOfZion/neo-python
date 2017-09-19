from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'53c56b6c766b00527ac46c766b51527ac461006c766b52527ac46c766b00c36c766b51c3a06c766b52527ac4616c7566'


class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b, c, d):

        m = 0

        if a > b:

            if c > d:

                m = 3

            else:

                m = 4

        else:

            if c > d:

                m = 1

            else:

                m = 2

        return m



