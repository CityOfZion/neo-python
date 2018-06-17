from neo.SmartContract.Iterable import EnumeratorBase


class StorageIterator(EnumeratorBase):
    pass

    # def __init__(self, enumerator):
    #     # returns a (key,value) tuple per iteration
    #     self.enumerator = enumerator
    #     self.key = None
    #     self.value = None
    #
    # def Dispose(self):
    #     pass
    #
    # def Key(self):
    #     """
    #     Get the key from the storage tuple of the current iteration.
    #
    #     Returns:
    #         StackItem: with the storage key.
    #     """
    #     return StackItem.New(self.key)
    #
    # def Next(self):
    #     """
    #     Advances the iterator forward 1 step.
    #
    #     Returns:
    #           bool: True if another item exists in the iterator, False otherwise.
    #     """
    #     try:
    #         self.key, self.value = next(self.enumerator)
    #     except StopIteration:
    #         return False
    #
    #     return True
    #
    # def Value(self):
    #     """
    #     Get the value from the storage tuple of the current iteration.
    #
    #     Returns:
    #         StackItem: with the storage value.
    #     """
    #     return StackItem.New(self.value)
