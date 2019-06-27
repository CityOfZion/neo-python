from neo.Storage.Interface.DBProperties import DBProperties
from neo.Storage.Common.DataCache import DataCache
import binascii
from neo.IO.MemoryStream import StreamManager
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.Core.IO.BinaryReader import BinaryReader


class LevelDBCache(DataCache):
    def __init__(self, db, batch, prefix, classref):
        super().__init__()
        self.db = db
        self.batch = batch
        self.prefix = prefix
        self.ClassRef = classref

    def AddInternal(self, key, value):
        if self.batch:
            stream = StreamManager.GetStream()
            bw = BinaryWriter(stream)
            value.Serialize(bw)

            self.batch.put(self.prefix + key, stream.ToArray())
            StreamManager.ReleaseStream(stream)

    def DeleteInternal(self, key):
        if self.batch:
            self.batch.delete(self.prefix + key)

    def FindInternal(self, key_prefix):
        key_prefix = self.prefix + key_prefix
        res = {}
        with self.DB.openIter(DBProperties(key_prefix, include_value=True)) as it:
            for key, val in it:
                # we want the storage item, not the raw bytes
                item = self.ClassRef.DeserializeFromDB(binascii.unhexlify(val)).Value
                # also here we need to skip the 1 byte storage prefix
                res_key = key[21:]
                res[res_key] = item
        return res

    def GetInternal(self, key):
        result = self.TryGetInternal(key)
        if result is None:
            raise ValueError("Key not found in DB!")

        return result
        # return self.db.get(self.prefix + key)

    def TryGetInternal(self, key):
        data = self.db.get(self.prefix + key)
        if data is None:
            return data

        data = binascii.unhexlify(data)

        stream = StreamManager.GetStream(data)
        br = BinaryReader(stream)
        obj = self.ClassRef()
        obj.Deserialize(br)
        StreamManager.ReleaseStream(stream)

        return obj

    def UpdateInternal(self, key, value):
        if self.batch:
            stream = StreamManager.GetStream()
            bw = BinaryWriter(stream)
            value.Serialize(bw)

            self.batch.put(self.prefix + key, stream.ToArray())
            StreamManager.ReleaseStream(stream)
