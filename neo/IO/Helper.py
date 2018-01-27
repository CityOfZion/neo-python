import importlib
from logzero import logger
from .MemoryStream import MemoryStream, StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neo.Core.TX.Transaction import Transaction
from neo.Blockchain import GetBlockchain


class Helper(object):

    @staticmethod
    def AsSerializableWithType(buffer, class_name):
        """

        Args:
            buffer (BytesIO/bytes): stream to deserialize `class_name` to.
            class_name (str): a full path to the class to be deserialized into. e.g. 'neo.Core.Block.Block'

        Returns:
            object: if deserialization is successful.
            None: if deserialization failed.
        """
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
            logger.error("Could not deserialize: %s %s" % (e, class_name))
        finally:
            StreamManager.ReleaseStream(mstream)

        return None

    @staticmethod
    def DeserializeTX(buffer):
        """
        Deserialize the stream into a Transaction object.

        Args:
            buffer (BytesIO): stream to deserialize the Transaction from.

        Returns:
            neo.Core.TX.Transaction:
        """
        mstream = MemoryStream(buffer)
        reader = BinaryReader(mstream)

        tx = Transaction.DeserializeFrom(reader)

        return tx
