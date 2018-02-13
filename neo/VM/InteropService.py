
from logzero import logger

from neo.VM.Mixins import EquatableMixin
from neocore.BigInteger import BigInteger


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
        return BigInteger(int.from_bytes(self.GetByteArray(), 'little', signed=True))

    def GetBoolean(self):
        for p in self.GetByteArray():
            if p > 0:
                return True
        return False

    def GetArray(self):
        logger.info("trying to get array:: %s " % self)
        raise Exception('Not supported')

    def GetInterface(self):
        return None

    def GetString(self):
        return 'Stack Item'

    def __str__(self):
        return 'Stack Item'

    @staticmethod
    def FromInterface(value):
        return InteropInterface(value)

    @staticmethod
    def New(value):
        typ = type(value)

        if typ is BigInteger:
            return Integer(value)
        elif typ is int:
            return Integer(BigInteger(value))
        elif typ is float:
            return Integer(BigInteger(int(value)))
        elif typ is bool:
            return Boolean(value)
        elif typ is bytearray or typ is bytes:
            return ByteArray(value)
        elif typ is list:
            return Array(value)

#        logger.info("Could not create stack item for vaule %s %s " % (typ, value))
        return value


class Array(StackItem):

    _array = []  # a list of stack items

    @property
    def IsArray(self):
        return True

    def __init__(self, value):
        self._array = value

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True
        if type(other) is not Array:
            return False

        return self._array == other._array

    def GetArray(self):
        return self._array

    def GetBigInteger(self):
        logger.info("Trying to get big integer %s " % self)
        raise Exception("Not Supported")

    def GetBoolean(self):
        return len(self._array) > 0

    def GetByteArray(self):
        logger.info("Trying to get bytearray integer %s " % self)

        raise Exception("Not supported")

    def __str__(self):
        return "Array: %s" % [str(item) for item in self._array]


class Boolean(StackItem):

    TRUE = bytearray([1])
    FALSE = bytearray([0])

    _value = None

    def __init__(self, value):
        self._value = value

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True

        if type(other) is not Boolean:
            return self.GetByteArray() == other.GetByteArray()

        return self._value == other._value

    def GetBigInteger(self):
        return 1 if self._value else 0

    def GetBoolean(self):
        return self._value

    def GetByteArray(self):
        return self.TRUE if self._value else self.FALSE

    def __str__(self):
        return "Boolean: %s" % self._value


class ByteArray(StackItem):

    _value = None

    def __init__(self, value):
        self._value = value

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True

        return self._value == other._value

    def GetBigInteger(self):
        try:
            b = BigInteger(int.from_bytes(self._value, 'little', signed=True))
            return b
        except Exception as e:
            pass
        return self._value

    def GetByteArray(self):
        return self._value

    def GetString(self):
        try:
            return self._value.decode('utf-8')
        except Exception as e:
            pass
        return str(self)

    def __str__(self):
        return "ByteArray: %s" % self._value


class Integer(StackItem):

    _value = None

    def __init__(self, value):
        if type(value) is not BigInteger:
            raise Exception("Must be big integer instance")
        self._value = value

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True

        if type(other) is not Integer:
            return self.GetByteArray() == other.GetByteArray()

        return self._value == other._value

    def GetBigInteger(self):
        return self._value

    def GetBoolean(self):
        return self._value != 0

    def GetByteArray(self):
        return self._value.ToByteArray()

    def __str__(self):
        return "Integer: %s " % self._value


class InteropInterface(StackItem):

    _object = None

    def __init__(self, value):
        self._object = value

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True

        if type(other) is not InteropInterface:
            return False

        return self._object == other._object

    def GetBoolean(self):
        return True if self._object is not None else False

    def GetByteArray(self):
        raise Exception("Not supported- Cant get byte array for item %s %s " % (type(self), self._object))

    def GetInterface(self):
        return self._object

    def __str__(self):
        try:
            return "IOp Interface: %s " % self._object
        except Exception as e:
            pass
        return "IOp Interface Item"


class Struct(Array):

    @property
    def IsStruct(self):
        return True

    def __init__(self, value):
        super(Struct, self).__init__(value)

    def Clone(self):
        length = len(self._array)
        newArray = [None for i in range(0, length)]

        for i in range(0, length):
            if self._array[i] is None:
                newArray[i] = None
            elif self._array[i].IsStruct:
                newArray[i] = self._array[i].Clone()
            else:
                newArray[i] = self._array[i]

        return Struct(newArray)

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True

        if type(other) is not Struct:
            return False
        return self._array == other._array

    def __str__(self):
        return "Struct: %s " % self._array


class InteropService():

    _dictionary = {}

    def __init__(self):
        self._dictionary = {}
        self.Register("System.ExecutionEngine.GetScriptContainer", self.GetScriptContainer)
        self.Register("System.ExecutionEngine.GetExecutingScriptHash", self.GetExecutingScriptHash)
        self.Register("System.ExecutionEngine.GetCallingScriptHash", self.GetCallingScriptHash)
        self.Register("System.ExecutionEngine.GetEntryScriptHash", self.GetEntryScriptHash)

    def Register(self, method, func):
        self._dictionary[method] = func

    def Invoke(self, method, engine):
        if method not in self._dictionary.keys():

            logger.info("method %s not found in ->" % method)
            for k, v in self._dictionary.items():
                logger.info("%s -> %s " % (k, v))
            return False

        func = self._dictionary[method]
        # logger.info("[InteropService Method] %s " % func)
        return func(engine)

    @staticmethod
    def GetScriptContainer(engine):
        engine.EvaluationStack.PushT(StackItem.FromInterface(engine.ScriptContainer))
        return True

    @staticmethod
    def GetExecutingScriptHash(engine):
        engine.EvaluationStack.PushT(engine.CurrentContext.ScriptHash())
        return True

    @staticmethod
    def GetCallingScriptHash(engine):
        engine.EvaluationStack.PushT(engine.CallingContext.ScriptHash())
        return True

    @staticmethod
    def GetEntryScriptHash(engine):

        engine.EvaluationStack.PushT(engine.EntryContext.ScriptHash())
        return True


def stack_item_to_py(stack_item):
    """
    Helper to convert a StackItem subclass to the specific Python object.
    eg. Integer(StackItem) -> int, or ByteArray(StackItem) -> bytes

    Works also with Array(StackItem).

    Args:
        stack_item (object): the StackItem subclass

    Returns:
        object: The StackItem subclass converted to it's native Python representation.
    """
    if isinstance(stack_item, Array):
        return [stack_item_to_py(item) for item in stack_item.GetArray()]

    elif isinstance(stack_item, Boolean):
        return stack_item.GetBoolean()

    elif isinstance(stack_item, ByteArray):
        return bytes(stack_item.GetByteArray())

    elif isinstance(stack_item, Integer):
        return stack_item.GetBigInteger()

    elif isinstance(stack_item, ByteArray):
        return stack_item.GetBigInteger()

    elif isinstance(stack_item, InteropInterface):
        return stack_item.GetInterface()

    elif isinstance(stack_item, Struct):
        return [stack_item_to_py(item) for item in stack_item.GetArray()]
    elif stack_item is None:
        return None
    else:
        raise ValueError('Not supported')
