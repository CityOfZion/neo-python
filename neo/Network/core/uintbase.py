import binascii
from neo.Network.core.mixin import serializable
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from neo.Network.core import BinaryReader
    from neo.Network.core.io.binary_writer import BinaryWriter


class UIntBase(serializable.SerializableMixin):
    _data = bytearray()
    _hash: int = 0

    def __init__(self, num_bytes: int, data: Union[bytes, bytearray] = None) -> None:
        super(UIntBase, self).__init__()

        if data is None:
            self._data = bytearray(num_bytes)

        else:
            if isinstance(data, bytes):
                # make sure it's mutable for string representation
                self._data = bytearray(data)
            elif isinstance(data, bytearray):
                self._data = data
            else:
                raise TypeError("Invalid data type {}. Expecting bytes or bytearray".format(type(data)))

            # now make sure we're working with raw bytes
            try:
                self._data = bytearray(binascii.unhexlify(self._data.decode()))
            except UnicodeDecodeError:
                # decode() fails most of the time if data is already in raw bytes. In that case there is nothing to be done.
                pass
            except binascii.Error:
                # however in some cases like bytes.fromhex('1122') decoding passes,
                # but binascii fails because it was actually already in rawbytes. Still nothing to be done.
                pass

            if len(self._data) != num_bytes:
                raise ValueError("Invalid UInt: data length {} != specified num_bytes {}".format(len(self._data), num_bytes))

        self._hash = self.get_hash_code()

    @property
    def size(self) -> int:
        """ Count of data bytes. """
        return len(self._data)

    def get_hash_code(self) -> int:
        """ Get a uint32 identifier. """
        slice_length = 4 if len(self._data) >= 4 else len(self._data)
        return int.from_bytes(self._data[:slice_length], 'little')

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        writer.write_bytes(self._data)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        self._data = reader.read_bytes(self.size)

    def to_array(self) -> bytearray:
        """ get the raw data. """
        return self._data

    def to_string(self) -> str:
        """ Convert the data to a human readable format (data is in reverse order). """
        db = bytearray(self._data)
        db.reverse()
        return db.hex()

    def __eq__(self, other) -> bool:
        if other is None:
            return False

        if not isinstance(other, UIntBase):
            return False

        if other is self:
            return True

        if self._data == other._data:
            return True

        return False

    def __hash__(self):
        return self._hash

    def __str__(self):
        return self.to_string()

    def _compare_to(self, other) -> int:
        if not isinstance(other, UIntBase):
            raise TypeError('Cannot compare %s to type %s' % (type(self).__name__, type(other).__name__))

        x = self.to_array()
        y = other.to_array()

        if len(x) != len(y):
            raise ValueError('Cannot compare %s with length %s to %s with length %s' % (type(self).__name__, len(x), type(other).__name__, len(y)))

        length = len(x)

        for i in range(length - 1, 0, -1):
            if x[i] > y[i]:
                return 1
            if x[i] < y[i]:
                return -1

        return 0

    def __lt__(self, other):
        return self._compare_to(other) < 0

    def __gt__(self, other):
        return self._compare_to(other) > 0

    def __le__(self, other):
        return self._compare_to(other) <= 0

    def __ge__(self, other):
        return self._compare_to(other) >= 0
