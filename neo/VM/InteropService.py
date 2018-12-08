import binascii
from neo.VM.Mixins import EquatableMixin
from neocore.BigInteger import BigInteger
from neo.SmartContract import StackItemType
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class CollectionMixin:
    IsSynchronized = False
    SyncRoot = None

    @property
    def Count(self):
        return 0

    def Contains(self, item):
        pass

    def Clear(self):
        pass

    def CopyTo(self, array, index):
        pass


class StackItem(EquatableMixin):

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
        logger.debug("trying to get array:: %s " % self)
        raise Exception('Not supported')

    def GetMap(self):
        return None

    def GetInterface(self):
        return None

    def GetString(self):
        return str(self)

    def Serialize(self, writer):
        pass

    #    def Deserialize(self, reader):
    #        pass

    def __hash__(self):
        hash = 17
        for b in self.GetByteArray():
            hash = hash * 31 + b
        #        print("hash code %s " % hash)
        return hash

    def __str__(self):
        return 'StackItem'

    def __eq__(self, other):
        return other and self.__hash__() == other.__hash__()

    @staticmethod
    def DeserializeStackItem(reader):
        stype = reader.ReadUInt8()
        if stype == StackItemType.ByteArray:
            return ByteArray(reader.ReadVarBytes())
        elif stype == StackItemType.Boolean:
            return Boolean(reader.ReadByte())
        elif stype == StackItemType.Integer:
            return Integer(BigInteger.FromBytes(reader.ReadVarBytes(), signed=True))
        elif stype == StackItemType.Array:
            stack_item = Array()
            count = reader.ReadVarInt()
            while count > 0:
                count -= 1
                stack_item.Add(StackItem.DeserializeStackItem(reader))
            return stack_item
        elif stype == StackItemType.Struct:
            stack_item = Struct(value=None)
            count = reader.ReadVarInt()
            while count > 0:
                count -= 1
                stack_item.Add(StackItem.DeserializeStackItem(reader))
            return stack_item
        elif stype == StackItemType.Map:
            stack_item = Map()
            count = reader.ReadVarInt()
            while count > 0:
                count -= 1
                key = StackItem.DeserializeStackItem(reader)
                val = StackItem.DeserializeStackItem(reader)
                stack_item.SetItem(key, val)
            return stack_item

        else:
            raise ValueError("Could not deserialize stack item with type: %s " % stype)

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

        #        logger.debug("Could not create stack item for vaule %s %s " % (typ, value))
        return value


class Array(StackItem, CollectionMixin):
    _array = None  # a list of stack items

    @property
    def Count(self):
        return len(self._array)

    def __init__(self, value=None):
        if value:
            self._array = value
        else:
            self._array = []

    def Clear(self):
        self._array = []

    def Contains(self, item):
        return item in self._array

    def Add(self, item):
        self._array.append(item)

    def Insert(self, index, item):
        self._array[index] = item

    def IndexOf(self, item):
        return self._array.index(item)

    def Remove(self, item):
        return self._array.remove(item)

    def RemoveAt(self, index):
        return self._array.pop(index)

    def Reverse(self):
        self._array.reverse()

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
        logger.debug("Trying to get big integer %s " % self)
        raise Exception("Not Supported")

    def GetBoolean(self):
        return len(self._array) > 0

    def GetByteArray(self):
        logger.debug("Trying to get bytearray integer %s " % self)

        raise Exception("Not supported")

    def GetEnumerator(self):
        return enumerate(self._array)

    def CopyTo(self, array, index):
        for item in self._array:
            array[index] = item
            index += 1

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.Array)
        writer.WriteVarInt(self.Count)
        for item in self._array:
            item.Serialize(writer)

    def __str__(self):
        return "Array: %s" % [str(item) for item in self._array]


class Boolean(StackItem):
    TRUE = bytearray([1])
    FALSE = bytearray([0])

    _value = None

    def __init__(self, value):
        self._value = value

    @property
    def Count(self):
        return 1

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

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.Boolean)
        writer.WriteByte(self.GetBigInteger())

    def __str__(self):
        return str(self._value)


class ByteArray(StackItem):
    _value = None

    def __init__(self, value):
        self._value = value

    @property
    def Count(self):
        return len(self._value)

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
            return binascii.unhexlify(self._value).decode('utf-8')
        except Exception as e:
            pass
        try:
            return self._value.decode('utf-8')
        except Exception as e:
            pass
        return self._value.hex()

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.ByteArray)
        writer.WriteVarBytes(self._value)

    def __str__(self):
        return self.GetString()


class Integer(StackItem):
    _value = None

    def __init__(self, value):
        if type(value) is not BigInteger:
            raise Exception("Must be big integer instance")
        self._value = value

    @property
    def Count(self):
        return 1

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

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.Integer)
        writer.WriteVarBytes(self.GetByteArray())

    def __str__(self):
        return str(self._value)


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

    def Serialize(self, writer):
        raise Exception('Not supported- Cannot serialize Interop Interface %s %s ' % (type(self), self._object))

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

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.Struct)
        writer.WriteVarInt(self.Count)
        for item in self._array:
            item.Serialize(writer)

    def __str__(self):
        return "Struct: %s " % self._array


class Map(StackItem, CollectionMixin):
    _dict = None

    def __init__(self, dict=None):
        if dict:
            self._dict = dict
        else:
            self._dict = {}

    @property
    def Keys(self):
        return list(self._dict.keys())

    @property
    def Values(self):
        return list(self._dict.values())

    @property
    def Count(self):
        return len(self._dict.keys())

    def GetItem(self, key):
        return self._dict[key]

    def SetItem(self, key, value):
        self._dict[key] = value

    def Add(self, key, value):
        self._dict[key] = value

    def Remove(self, key):
        del self._dict[key]
        return True

    def Clear(self):
        self._dict = {}

    def ContainsKey(self, key):
        return key in self._dict

    def Contains(self, item):
        return item in self._dict.values()

    def CopyTo(self, array, index):
        for key, value in self._dict.items():
            array[index] = (key, value)
            index += 1

    def TryGetValue(self, key):
        if key in self._dict.keys():
            return True, self._dict[key]
        return False, None

    def Equals(self, other):
        if other is None:
            return False
        if other is self:
            return True
        if type(other) is not Map:
            return False
        return self._dict == other._dict

    def __eq__(self, other):
        return self.Equals(other)

    def __str__(self):
        return self.GetString()

    def GetBoolean(self):
        return True

    def GetMap(self):
        return self._dict

    def GetEnumerator(self):
        return iter(self._dict.items())

    def Serialize(self, writer):
        writer.WriteByte(StackItemType.Map)
        writer.WriteVarInt(self.Count)
        for key, val in self._dict.items():
            key.Serialize(writer)
            val.Serialize(writer)

    def GetString(self):
        return dict((k.GetString(), v.GetString()) for k, v in self._dict.items())

    def GetByteArray(self):
        raise Exception("Not supported- Cant get byte array for item %s %s " % (type(self), self._dict))


class InteropService:
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
            logger.debug("method %s not found" % method)
        func = self._dictionary[method]
        return func(engine)

    @staticmethod
    def GetScriptContainer(engine):
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(engine.ScriptContainer))
        return True

    @staticmethod
    def GetExecutingScriptHash(engine):
        engine.CurrentContext.EvaluationStack.PushT(engine.CurrentContext.ScriptHash())
        return True

    @staticmethod
    def GetCallingScriptHash(engine):
        engine.CurrentContext.EvaluationStack.PushT(engine.CallingContext.ScriptHash())
        return True

    @staticmethod
    def GetEntryScriptHash(engine):
        engine.CurrentContext.EvaluationStack.PushT(engine.EntryContext.ScriptHash())
        return True
