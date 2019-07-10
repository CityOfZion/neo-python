import sys
import struct
from typing import Union, Any
from neo.Network.core.uint256 import UInt256
from neo.Network.core.uint160 import UInt160
from neo.IO.MemoryStream import StreamManager


class BinaryReader(object):
    """A convenience class for reading data from byte streams"""

    def __init__(self, stream: Union[bytes, bytearray]) -> None:
        """
        Create an instance.

        Args:
            stream (BytesIO, bytearray): a stream to operate on.
        """
        super(BinaryReader, self).__init__()
        self._stream = StreamManager.GetStream(stream)

    def _unpack(self, fmt, length=1) -> Any:
        """
        Unpack the stream contents according to the specified format in `fmt`.
        For more information about the `fmt` format see: https://docs.python.org/3/library/struct.html

        Args:
            fmt (str): format string.
            length (int): amount of bytes to read.

        Returns:
            variable: the result according to the specified format.
        """
        try:
            values = struct.unpack(fmt, self._stream.read(length))
            return values[0]
        except struct.error as e:
            raise ValueError(e)

    def read_byte(self) -> bytes:
        """
        Read a single byte.

        Raises:
            ValueError: if 1 byte of data cannot be read from the stream

        Returns:
            bytes: a single byte.
        """
        value = self._stream.read(1)
        if len(value) != 1:
            raise ValueError("Could not read byte from empty stream")
        return value

    def read_bytes(self, length: int) -> bytes:
        """
        Read the specified number of bytes from the stream.

        Args:
            length (int): number of bytes to read.

        Returns:
            bytes: `length` number of bytes.
        """
        value = self._stream.read(length)
        if len(value) != length:
            raise ValueError("Could not read {} bytes from stream. Only found {} bytes of data".format(length, len(value)))

        return value

    def read_bool(self) -> bool:
        """
        Read 1 byte as a boolean value from the stream.

        Returns:
            bool:
        """
        return self._unpack('?')

    def read_uint8(self, endian="<"):
        """
        Read 1 byte as an unsigned integer value from the stream.

        Args:
            endian (str): specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.

        Returns:
            int:
        """
        return self._unpack('%sB' % endian)

    def read_uint16(self, endian="<"):
        """
        Read 2 byte as an unsigned integer value from the stream.

        Args:
            endian (str): specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.

        Returns:
            int:
        """
        return self._unpack('%sH' % endian, 2)

    def read_uint32(self, endian="<"):
        """
        Read 4 bytes as an unsigned integer value from the stream.

        Args:
            endian (str): specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.

        Returns:
            int:
        """
        return self._unpack('%sI' % endian, 4)

    def read_uint64(self, endian="<"):
        """
        Read 8 bytes as an unsigned integer value from the stream.

        Args:
            endian (str): specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.

        Returns:
            int:
        """
        return self._unpack('%sQ' % endian, 8)

    def read_var_int(self, max=sys.maxsize) -> int:
        """
        Read a variable length integer from the stream.
        The NEO network protocol supports encoded storage for space saving. See: http://docs.neo.org/en-us/node/network-protocol.html#convention

        Args:
            max: (Optional) maximum number of bytes to read.

        Returns:
            int:
        """
        fb = int.from_bytes(self.read_byte(), 'little')
        if fb is 0:
            return fb

        if fb == 0xfd:
            value = self.read_uint16()
        elif fb == 0xfe:
            value = self.read_uint32()
        elif fb == 0xff:
            value = self.read_uint64()
        else:
            value = fb

        if value > max:
            raise ValueError("Invalid format")

        return value

    def read_var_bytes(self, max=sys.maxsize):
        """
        Read a variable length of bytes from the stream.
        The NEO network protocol supports encoded storage for space saving. See: http://docs.neo.org/en-us/node/network-protocol.html#convention

        Args:
            max (int): (Optional) maximum number of bytes to read.

        Returns:
            bytes:
        """
        length = self.read_var_int(max)
        return self.read_bytes(length)

    def read_var_string(self, max=sys.maxsize) -> str:
        """
        Similar to `ReadString` but expects a variable length indicator instead of the fixed 1 byte indicator.

        Args:
            max (int): (Optional) maximum number of bytes to read.

        Returns:
            bytes:
        """
        length = self.read_var_int(max)
        try:
            data = self._unpack(str(length) + 's', length)
            return data.decode('utf-8')

        except UnicodeDecodeError as e:
            raise e
        except Exception as e:
            raise e

    def read_fixed_string(self, length: int) -> str:
        """
        Read a fixed length string from the stream.

        Args:
            length (int): length of string to read.

        Raises:
            ValueError: if not enough data could be read from the stream

        Returns:
            str:
        """
        return self.read_bytes(length).rstrip(b'\x00')

    def read_uint256(self):
        """
        Read a UInt256 value from the stream.

        Returns:
            UInt256:
        """
        return UInt256(data=bytearray(self.read_bytes(32)))

    def read_uint160(self):
        """
        Read a UInt160 value from the stream.

        Returns:
            UInt160:
        """
        return UInt160(data=bytearray(self.read_bytes(20)))

    def cleanup(self):
        if self._stream:
            StreamManager.ReleaseStream(self._stream)
