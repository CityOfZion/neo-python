from neo.UIntBase import UIntBase

class UInt160(UIntBase):




    def __init__(self, data=None):

        super(UInt160, self).__init__(num_bytes=20, data=data)





    def CompareTo(self, other):

        x = self.ToArray()
        y = other.ToArray()

        length = len(x)

        for i in range(length-1, 0, -1):

            if x[i] > y[i]:
                return 1
            if x[i] < y[i]:
                return -1

        return 0


    def __lt__(self, other):
        return self.CompareTo(other) < 0

    def __gt__(self, other):
        return self.CompareTo(other) > 0

    def __le__(self, other):
        return self.CompareTo(other) <= 0

    def __ge__(self, other):
        return self.CompareTo(other) >= 0