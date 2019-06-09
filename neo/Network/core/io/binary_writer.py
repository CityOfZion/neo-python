import struct
import binascii
import io
from typing import Union
from neo.IO.MemoryStream import StreamManager


class BinaryWriter(object):
    """A convenience class for writing data from byte streams"""

    def __init__(self, stream: Union[bytearray, bytes]) -> None:
        """
        Create an instance.

        Args:
            stream: a stream to operate on.
        """
        super(BinaryWriter, self).__init__()
        self._stream = StreamManager.GetStream(stream)

    def write_bytes(self, value: bytes, unhex: bool = True) -> int:
        """
        Write a `bytes` type to the stream.
        Args:
            value: array of bytes to write to the stream.
            unhex: (Default) True. Set to unhexlify the stream. Use when the bytes are not raw bytes; i.e. b'aabb'
        Returns:
            int: the number of bytes written.
        """
        if unhex:
            try:
                value = binascii.unhexlify(value)
            except binascii.Error:
                pass
        return self._stream.write(value)

    def _pack(self, fmt, data) -> int:
        """
        Write bytes by packing them according to the provided format `fmt`.
        For more information about the `fmt` format see: https://docs.python.org/3/library/struct.html
        Args:
            fmt (str): format string.
            data (object): the data to write to the raw stream.
        Returns:
            int: the number of bytes written.
        """
        return self.write_bytes(struct.pack(fmt, data), unhex=False)

    def write_bool(self, value: bool) -> int:
        """
        Pack the value as a bool and write 1 byte to the stream.
        Args:
            value: the boolean value to write.
        Returns:
            int: the number of bytes written.
        """
        return self._pack('?', value)

    def write_uint8(self, value):
        return self.write_bytes(bytes([value]))

    def write_uint16(self, value, endian="<"):
        """
        Pack the value as an unsigned integer and write 2 bytes to the stream.
        Args:
            value:
            endian: specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.
        Returns:
            int: the number of bytes written.
        """
        return self._pack('%sH' % endian, value)

    def write_uint32(self, value, endian="<") -> int:
        """
        Pack the value as a signed integer and write 4 bytes to the stream.
        Args:
            value:
            endian: specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.
        Returns:
            int: the number of bytes written.
        """
        return self._pack('%sI' % endian, value)

    def write_uint64(self, value, endian="<") -> int:
        """
        Pack the value as an unsigned integer and write 8 bytes to the stream.
        Args:
            value:
            endian (str): specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.
        Returns:
            int: the number of bytes written.
        """
        return self._pack('%sQ' % endian, value)

    def write_uint256(self, value, endian="<") -> int:
        return self.write_bytes(value._data)

    def write_uint160(self, value, endian="<") -> int:
        return self.write_bytes(value._data)

    def write_var_string(self, value: str, encoding: str = "utf-8") -> int:
        """
        Write a string value to the stream.
        Read more about variable size encoding here: http://docs.neo.org/en-us/node/network-protocol.html#convention
        Args:
            value: value to write to the stream.
            encoding: string encoding format.
        """
        if type(value) is str:
            data = value.encode(encoding)

        length = len(data)
        self.write_var_int(length)
        written = self.write_bytes(data)
        return written

    def write_var_int(self, value: int, endian: str = "<") -> int:
        """
        Write an integer value in a space saving way to the stream.
        Read more about variable size encoding here: http://docs.neo.org/en-us/node/network-protocol.html#convention
        Args:
            value:
            endian: specify the endianness. (Default) Little endian ('<'). Use '>' for big endian.
        Raises:
            {TypeError}: if ``value`` is not of type int.
            ValueError: if `value` is < 0.
        Returns:
            int: the number of bytes written.
        """
        if not isinstance(value, int):
            raise TypeError('%s not int type.' % value)

        if value < 0:
            raise ValueError('%d too small.' % value)

        elif value < 0xfd:
            return self.write_bytes(bytes([value]))

        elif value <= 0xffff:
            self.write_bytes(bytes([0xfd]))
            return self.write_uint16(value, endian)

        elif value <= 0xFFFFFFFF:
            self.write_bytes(bytes([0xfe]))
            return self.write_uint32(value, endian)

        else:
            self.write_bytes(bytes([0xff]))
            return self.write_uint64(value, endian)

    def write_fixed_string(self, value, length):
        """
        Write a string value to the stream.
        Args:
            value (str): value to write to the stream.
            length (int): length of the string to write.
        """
        towrite = value.encode('utf-8')
        slen = len(towrite)
        if slen > length:
            raise Exception("string longer than fixed length: %s " % length)
        self.write_bytes(towrite)
        diff = length - slen

        while diff > 0:
            self.write_bytes(bytes([0]))
            diff -= 1

    def write_var_bytes(self, value: int, endian: str = "<") -> int:
        self.write_var_int(len(value), endian)
        return self.write_bytes(value)

    def cleanup(self):
        if self._stream:
            StreamManager.ReleaseStream(self._stream)
