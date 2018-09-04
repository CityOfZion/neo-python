from enum import IntEnum, Enum
from collections import Iterable
from neocore.IO.Mixins import SerializableMixin
from neocore.UIntBase import UIntBase

"""
This helper class is intended to help resolve the correct calculation of network serializable objects.
The result of `ctypes.sizeof` is not equivalent to C# or what we expect. See https://github.com/CityOfZion/neo-python/pull/418#issuecomment-389803377
for more discussion on the topic.
"""


class Size(IntEnum):
    """
    Explicit bytes of memory consumed
    """
    uint8 = 1
    uint16 = 2
    uint32 = 4
    uint64 = 8
    uint160 = 20
    uint256 = 32


def GetVarSize(value):
    # public static int GetVarSize(this string value)
    if isinstance(value, str):
        value_size = len(value.encode('utf-8'))
        return GetVarSize(value_size) + value_size

    # internal static int GetVarSize(int value)
    elif isinstance(value, int):
        if (value < 0xFD):
            return Size.uint8
        elif (value <= 0xFFFF):
            return Size.uint8 + Size.uint16
        else:
            return Size.uint8 + Size.uint32

    # internal static int GetVarSize<T>(this T[] value)
    elif isinstance(value, Iterable):
        value_length = len(value)
        value_size = 0

        if value_length > 0:
            if isinstance(value[0], SerializableMixin):
                if isinstance(value[0], UIntBase):
                    # because the Size() method in UIntBase is implemented as a property
                    value_size = sum(map(lambda t: t.Size, value))
                else:
                    value_size = sum(map(lambda t: t.Size(), value))

            elif isinstance(value[0], Enum):
                # Note: currently all Enum's in neo core (C#) are of type Byte. Only porting that part of the code
                value_size = value_length * Size.uint8
            elif isinstance(value, (bytes, bytearray)):
                # experimental replacement for: value_size = value.Length * Marshal.SizeOf<T>();
                # because I don't think we have a reliable 'SizeOf' in python
                value_size = value_length * Size.uint8
            else:
                raise Exception("Can not accurately determine size of objects that do not inherit from 'SerializableMixin', 'Enum' or 'bytes'. Found type: {}".format(type(value[0])))

    else:
        raise Exception("[NOT SUPPORTED] Unexpected value type {} for GetVarSize()".format(type(value)))

    return GetVarSize(value_length) + value_size
