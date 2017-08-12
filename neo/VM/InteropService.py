
from neo.VM.Mixins import EquatableMixin
from neo.BigInteger import BigInteger



class StackItem(EquatableMixin):


    @property
    def IsArray(self):
        return False

    @property
    def IsStruct(self):
        return False

    def GetByteArray(self):
        return bytearray()

    def GetBigInteger(self):
        return BigInteger(int.from_bytes(self.GetByteArray(),'little'))

    def GetBoolean(self):
        for p in self.GetByteArray():
            if p > 0: return True
        return False

    def GetArray(self):
        raise Exception('Not supported')

    def GetInterface(self, t):
        raise Exception('Not Supported')


    @staticmethod
    def FromInterface(value):
        return InteropInterface(value)


    @staticmethod
    def New(value):
        typ = type(value)

        if typ is BigInteger:
            return Integer(value)
        elif typ is int:
            return Integer( BigInteger(value))
        elif typ is bool:
            return Boolean(value)
        elif typ is bytearray:
            return ByteArray(value)
        elif typ is list:
            return Array(value)

class Array(StackItem):


    _array = [] # a list of stack items


    def IsArray(self):
        return True

    def __init__(self, value):
        self._array = value

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        if type(other) is not Array:
            return False

        return self._array == other._array

    def GetArray(self):
        return self._array

    def GetBigInteger(self):
        raise Exception("Not Supported")

    def GetBoolean(self):
        return len(self._array) > 0

    def GetByteArray(self):
        raise Exception("Not supported")



class Boolean(StackItem):

    TRUE = bytearray([1])
    FALSE = bytearray([0])

    _value = None

    def __init__(self, value):
        self._value = value

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        if type(other) is not Boolean:
            return self.GetByteArray() == other.GetByteArray()

        return self._value == other._value


    def GetBigInteger(self):
        return 1 if self._value else 0

    def GetBoolean(self):
        return self._value

    def GetByteArray(self):
        return self.TRUE if self._value else self.FALSE




class ByteArray(StackItem):


    _value = None

    def __init__(self, value):
        self._value = value

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        return self._value == other._value


    def GetByteArray(self):
        return self._value


class Integer(StackItem):


    _value = None

    def __init__(self, value):
        if type(value) is not BigInteger:
            raise Exception("Must be big integer instance")
        self._value = value

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        if type(other) is not Integer:
            return self.GetByteArray() == other.GetByteArray()

        return self._value == other._value


    def GetBigInteger(self):
        return self._value

    def GetBoolean(self):
        return self._value != 0

    def GetByteArray(self):
        return self._value.ToByteArray()


class InteropInterface(StackItem):

    _object = None

    def __init__(self, value):
        self._object = value

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        if type(other) is not InteropInterface:
            return False

        return self._object == other._object

    def GetBoolean(self):
        return True if self._object is not None else False

    def GetByteArray(self):
        raise Exception("Not supported!")

    def GetInterface(self, t):
        return self._object



class Struct(Array):

    def IsStruct(self):
        return True

    def __init__(self, value):
        super(Struct, self).__init__(value)

    def Clone(self):
        newArray = []

        for i in range(0, len(self._array)):
            if self._array[i].IsStruct:
                newArray[i] = self._array[i].Clone()
            else:
                newArray[i] = self._array[i]

        return Struct(newArray)

    def Equals(self, other):
        if other is None: return False
        if other is self: return True

        if type(other) is not Struct:
            return False
        return self._array == other._array

class InteropService():


    _dictionary = {}


    def _Register(self, method, func):
        self._dictionary[method] = func

    def _Invoke(self, method, engine):

        if not method in self._dictionary.keys():

            return False

        func = self._dictionary[method]

        return func(engine)

    @staticmethod
    def GetScriptContainer(engine):

        engine.EvaluationStack.Push( StackItem.FromInterface(engine.ScriptContainer))
        return True

    @staticmethod
    def GetExecutingScriptHash(engine):
        engine.EvaluationStack.Push( engine.CurrentContext.ScriptHash )
        return True

    @staticmethod
    def GetCallingScriptHash(engine):
        engine.EvaluationStack.Push( engine.CallingContext.ScriptHash )
        return True

    @staticmethod
    def GetEntryScriptHash(engine):
        engine.EvaluationStack.Push( engine.EntryContext.ScriptHash )
        return True
