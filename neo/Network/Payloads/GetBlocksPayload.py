import sys

from logzero import logger

from neo.IO.Mixins import SerializableMixin
from neo.UInt256 import UInt256


class GetBlocksPayload(SerializableMixin):

    HashStart = []
    HashStop = None

    def __init__(self, hash_start=[], hash_stop=None):

        self.HashStart = hash_start
        self.HashStop = hash_stop

    def Size(self):
        return sys.getsizeof(self.HashStart) + sys.getsizeof(self.HashStop)

    def Deserialize(self, reader):
        self.HashStart = reader.ReadHashes()
        self.HashStop = reader.ReadUInt256()

    def Serialize(self, writer):
        #        logger.info("Writing hash start... %s %s" % (len(self.HashStart), self.HashStart[0].ToArray()))
        writer.WriteHashes(self.HashStart)
        if self.HashStop is not None:
            writer.WriteUInt256(self.HashStop)
#        else:
#            writer.WriteUInt256( UInt256(data=bytearray(32)))
#        logger.info("Wrote Hash start ...")
