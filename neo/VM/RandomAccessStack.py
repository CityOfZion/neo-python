from neo.VM.InteropService import StackItem
from autologging import logged

@logged
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

    def Peek(self, index = 0):
        index = int(index)

        if index < 0 or index > self.Count:
            raise Exception("Invalid list operation")

        return self._list[self.Count - 1 - index]

    def Pop(self):
#        self.PrintList("POPSTACK <- ")
        return self.Remove(0)

    def PushT(self, item):
        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            try:
                item = StackItem.New(item)
            except Exception as e:
                self.__log.debug("Could not create stack item from %s %s " % (item, type(item)))

        self.PrintFormat('PUSHT', item)
        self._list.append(item)

    def Remove(self, index):
        index = int(index)

        if index < 0 or index >= self.Count:
            raise Exception("Invalid list operation")

        item = self._list.pop( self.Count - 1 - index )

        return item


    def Set(self, index, item):
        index = int(index)

        if index < 0 or index > self.Count:
            raise Exception("Invalid list operation")

        if not type(item) is StackItem and not issubclass(type(item), StackItem):
            try:
                item = StackItem.New(item)
            except Exception as e:
                self.__log.debug("Could not create stack item from %s %s " % (item, type(item)))

        self.PrintFormat('SET',item)

        self._list[self.Count - index - 1] = item

    def PrintFormat(self, operation, value):
        name = "{:<15}".format("[%s]" % self._name)
        op = "{:<10}".format(operation)
        self.__log.debug("                                         %s  %s -> %s" % (name,op, value))


    def PrintList(self, message=None):
        print("%s %s" % (message,[str(item) for item in self._list]))