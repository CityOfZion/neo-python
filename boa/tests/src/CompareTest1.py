from neo.SmartContract.Framework.FunctionCode import FunctionCode


class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b, c, d):

        m = 0

        if a > b:

            if c > d:

                m = 3

            else:

                if b > c:

                    return 8

                else:

                    return 10

        else:

            if c > d:

                m = 1

            else:

                if b < c:

                    return 11

                else:

                    m = 22

        return m



