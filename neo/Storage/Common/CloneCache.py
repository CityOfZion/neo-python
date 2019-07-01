from neo.Storage.Common.DataCache import DataCache


class CloneCache(DataCache):
    def __init__(self, innerCache):
        super(CloneCache, self).__init__()
        self.innerCache = innerCache

    def AddInternal(self, key, value):
        self.innerCache.Add(key, value)

    def DeleteInternal(self, key):
        self.innerCache.Delete(key)

    def FindInternal(self, key_prefix):
        for k, v in self.innerCache.Find(key_prefix):
            yield k, v.Clone()

    def GetInternal(self, key):
        return self.innerCache[key].Clone()

    def TryGetInternal(self, key):
        res = self.innerCache.TryGet(key)
        if res is None:
            return None
        else:
            return res.Clone()

    def UpdateInternal(self, key, value):
        self.innerCache.GetAndChange(key).FromReplica(value)
