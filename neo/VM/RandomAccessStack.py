from neo.VM.InteropService import StackItem


class RandomAccessStack:

    _list = []
    _size = 0  # cache the size for performance

    _name = 'Stack'

    def __init__(self, name='Stack'):
        self._list = []
        self._size = 0
        self._name = name

    @property
    def Count(self):
        return self._size

    @property
    def Items(self):
        return self._list

    def Clear(self):
        self._list = []
        self._size = 0

    def GetEnumerator(self):
        return enumerate(self._list)

    def Insert(self, index, item):
        index = int(index)

        if index < 0 or index > self._size:
            raise Exception("Invalid list operation")

        self._list.insert(index, item)
        self._size += 1

    # @TODO can be optimized
    def Peek(self, index=0):
        index = int(index)
        if index >= self._size:
            raise Exception("Invalid list operation")

        return self._list[self._size - 1 - index]

    def Pop(self):
        #        self.PrintList("POPSTACK <- ")
        return self.Remove(0)

    def PushT(self, item):
        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            item = StackItem.New(item)

        self._list.append(item)
        self._size += 1

    # @TODO can be optimized
    def Remove(self, index):
        index = int(index)

        if index < 0 or index >= self._size:
            raise Exception("Invalid list operation")

        item = self._list.pop(self._size - 1 - index)
        self._size -= 1

        return item

    def Set(self, index, item):
        index = int(index)

        if index < 0 or index > self._size:
            raise Exception("Invalid list operation")

        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            item = StackItem.New(item)

        self._list[self._size - index - 1] = item
