import importlib
from logzero import logger
from .MemoryStream import MemoryStream, StreamManager
from .BinaryReader import BinaryReader
from neo.Core.TX.Transaction import Transaction


class Helper(object):

    @staticmethod
    def AsSerializableWithType(buffer, class_name):
        module = '.'.join(class_name.split('.')[:-1])
        klassname = class_name.split('.')[-1]
        klass = getattr(importlib.import_module(module), klassname)
        mstream = StreamManager.GetStream(buffer)
        reader = BinaryReader(mstream)

        try:
            serializable = klass()
            serializable.Deserialize(reader)
            return serializable
        except Exception as e:
            logger.error("couldnt deserialize: %s " % e)
        finally:
            StreamManager.ReleaseStream(mstream)

        return None

    @staticmethod
    def DeserializeTX(buffer):
        mstream = MemoryStream(buffer)
        reader = BinaryReader(mstream)

        tx = Transaction.DeserializeFrom(reader)

        return tx

    @staticmethod
    def GetVarSize(iterator):
        """
        Get length of a variable sized input.

        Args:
            iterator(iterator)

        Returns:
            int: length
        """
        value_len = len(iterator)

        result = value_len
        if (value_len < 0xFD):
            result += 1  # byte
        elif (value_len <= 0xFFF):
            result += 3  # byte + ushort
        else:
            result += 5  # byte + int
        return result
