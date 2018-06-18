from abc import ABC, abstractmethod
from neo.VM.Mixins import InteropMixin
from neo.VM.InteropService import StackItem


class Enumerator(ABC, InteropMixin):

    @abstractmethod
    def Next(self) -> bool:
        pass

    @abstractmethod
    def Value(self) -> StackItem:
        pass

    @abstractmethod
    def Dispose(self):
        pass


class Iterator(Enumerator):

    def Key(self) -> StackItem:
        pass

    def Dispose(self):
        pass


class ValuesWrapper(Enumerator):

    def __init__(self, iterator):

        self.iterator = iterator

    def Dispose(self):
        self.iterator.Dispose()

    def Next(self):
        return self.iterator.Next()

    def Value(self):
        return self.iterator.Value()


class KeysWrapper(Enumerator):

    def __init__(self, iterator):
        self.iterator = iterator

    def Dispose(self):
        self.iterator.Dispose()

    def Next(self):
        return self.iterator.Next()

    def Value(self):
        return self.iterator.Key()


class EnumeratorBase(Iterator):

    enumerator = None

    def __init__(self, item):
        self.enumerator = item
        self.value = None
        self.key = None

    def Key(self):
        return StackItem.New(self.key)

    def Next(self):
        try:
            self.key, self.value = next(self.enumerator)
        except StopIteration:
            return False
        return True

    def Value(self):
        return StackItem.New(self.value)
