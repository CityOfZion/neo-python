from neo.SmartContract.Iterable import Iterator
from neo.VM.InteropService import StackItem


class StorageIterator(Iterator):
    def __init__(self, enumerator):
        self.enumerator = enumerator
        self.key = None
        self.value = None

    def Key(self):
        return StackItem.New(self.key)

    def Next(self):
        try:
            self.key, self.value = next(self.enumerator)
            self.key = self.key[20:]
        except StopIteration:
            return False
        return True

    def Value(self):
        return StackItem.New(self.value.Value)
