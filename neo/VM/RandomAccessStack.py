from neo.VM.InteropService import StackItem


class RandomAccessStack():

    _list = []

    _name = 'Stack'

    def __init__(self, name='Stack'):
        self._list = []
        self._name = name

    @property
    def Count(self):
        return len(self._list)

    @property
    def Items(self):
        return self._list

    def Clear(self):
        self._list = []

    def GetEnumerator(self):
        return enumerate(self._list)

    def Insert(self, index, item):
        index = int(index)

        if index < 0 or index > self.Count:
            raise Exception("Invalid list operation")

        self._list.insert(index, item)

    def Peek(self, index=0):
        index = int(index)
        if index >= self.Count:
            raise Exception("Invalid list operation")

        return self._list[self.Count - 1 - index]

    def Pop(self):
        #        self.PrintList("POPSTACK <- ")
        return self.Remove(0)

    def PushT(self, item):
        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            item = StackItem.New(item)

        self._list.append(item)

    def Remove(self, index):
        index = int(index)

        if index < 0 or index >= self.Count:
            raise Exception("Invalid list operation")

        item = self._list.pop(self.Count - 1 - index)

        return item

    def Set(self, index, item):
        index = int(index)

        if index < 0 or index > self.Count:
            raise Exception("Invalid list operation")

        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            item = StackItem.New(item)

        self._list[self.Count - index - 1] = item
