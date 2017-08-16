

class UInt160(int):


    _data = bytearray()


    def __init__(self, x=None, base=10, data=None):
        super(UInt160, self).__init__(x, base)

        self._data = data

