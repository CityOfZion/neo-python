from neo.SmartContract.Iterable import Iterator
from neo.SmartContract.Iterable.ArrayWrapper import ArrayWrapper
from neo.VM.InteropService import StackItem


class ConcatenatedIterator(Iterator):
    def __init__(self, first, second):
        if first == second:
            new_list = []
            while first.Next():
                new_list.append(first.Value())

            first = ArrayWrapper(new_list)
            second = ArrayWrapper(new_list)

        self.first = first
        self.current = self.first
        self.second = second

    def Key(self) -> StackItem:
        return self.current.Key()

    def Value(self) -> StackItem:
        return self.current.Value()

    def Next(self) -> bool:
        if self.current.Next():
            return True

        self.current = self.second
        return self.current.Next()

    def Dispose(self):
        pass
