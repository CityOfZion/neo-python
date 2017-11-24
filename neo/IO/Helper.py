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
