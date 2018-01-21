from neocore.IO.Mixins import SerializableMixin
import sys


class HeadersPayload(SerializableMixin):
    Headers = []

    def __init__(self, headers=None):
        """
        Create an instance.

        Args:
            headers (list): of neo.Core.Header.Header objects.
        """
        self.Headers = headers if headers else []

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return sys.getsizeof(self.Headers)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Headers = reader.ReadSerializableArray('neo.Core.Header.Header')

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.Write(self.Headers)
