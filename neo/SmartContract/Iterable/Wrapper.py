from neo.SmartContract.Iterable import EnumeratorBase
from neo.VM.InteropService import Array, Map


class ArrayWrapper(EnumeratorBase):

    def __init__(self, array: Array):
        super(ArrayWrapper, self).__init__(array)
        self.enumerator = array.GetEnumerator()


class MapWrapper(EnumeratorBase):

    def __init__(self, map: Map):
        super(MapWrapper, self).__init__(map)
        self.enumerator = map.GetEnumerator()
