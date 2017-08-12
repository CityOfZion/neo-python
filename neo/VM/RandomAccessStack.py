
class RandomAccessStack():


    _list = []

    def __init__(self):
        self._list = []

    def Count(self):
        return len(self._list)

    def Clear(self):
        self._list = []

    def GetEnumerator(self):
        return enumerate(self._list)


    def Insert(self, index, item):
        index = int(index)

        if index < 0 or index > self.Count():
            raise Exception("Invalid list operation")

        self._list.insert(index, item)

    def Peek(self, index = 0):
        index = int(index)

        if index < 0 or index > self.Count():
            raise Exception("Invalid list operation")

        return self._list[self.Count() - 1 - index]

    def Pop(self):
        return self._list.pop(0)

    def PushT(self, item):
        self._list.append(item)

    def Remove(self, index):
        index = int(index)

        if index < 0 or index > self.Count():
            raise Exception("Invalid list operation")

        item = self._list[self.Count() - 1 - index]

        item = self._list.remove(item)

        return item


    def Set(self, index, item):
        index = int(index)

        if index < 0 or index > self.Count():
            raise Exception("Invalid list operation")

        self._list[self.Count() - index - 1] = item