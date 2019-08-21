from neo.SmartContract.Iterable import Iterator


class ArrayWrapper(Iterator):
    def __init__(self, array):
        self.array = array
        self.index = -1

    def Dispose(self):
        pass

    def Key(self):
        if self.index < 0:
            raise ValueError
        return self.index

    def Next(self) -> bool:
        next = self.index + 1
        if next >= len(self.array):
            return False
        self.index = next
        return True

    def Value(self):
        if self.index < 0:
            raise ValueError
        return self.array[self.index]
