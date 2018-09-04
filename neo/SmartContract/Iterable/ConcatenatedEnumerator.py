from neo.SmartContract.Iterable import Enumerator
from neo.VM.InteropService import StackItem


class ConcatenatedEnumerator(Enumerator):

    def __init__(self, first, second):
        # returns a (key,value) tuple per iteration
        self.first = first.enumerator
        self.second = second.enumerator
        self.current = self.first

        self.key = None
        self.value = None

    def Dispose(self):
        pass

    def Next(self):
        """
        Advances the iterator forward 1 step.

        Returns:
              bool: True if another item exists in the iterator, False otherwise.
        """
        try:
            self.key, self.value = next(self.current)
        except StopIteration:

            if self.current != self.second:
                self.current = self.second
                return self.Next()

            return False

        return True

    def Value(self):
        """
        Get the value from the storage tuple of the current iteration.

        Returns:
            StackItem: with the storage value.
        """
        return StackItem.New(self.value)
