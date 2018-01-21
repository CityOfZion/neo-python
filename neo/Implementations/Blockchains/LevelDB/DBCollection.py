import binascii
from logzero import logger


class DBCollection():

    DB = None
#    SN = None
    Prefix = None

    ClassRef = None

    Collection = {}

    Changed = []
    Deleted = []

    _built_keys = False

    DebugStorage = False

    def __init__(self, db, sn, prefix, class_ref):

        self.DB = db

        self.Prefix = prefix

        self.ClassRef = class_ref

        self.Collection = {}
        self.Changed = []
        self.Deleted = []

    @property
    def Keys(self):
        if not self._built_keys:
            self._BuildCollectionKeys()

        return self.Collection.keys()

    @property
    def Current(self):
        try:
            ret = {}
            for key, val in self.Collection.items():
                if val is not None:
                    ret[key] = val
            return ret
        except Exception as e:
            logger.error("error getting items %s " % e)

        return {}

    def _BuildCollectionKeys(self):
        for key in self.DB.iterator(prefix=self.Prefix, include_value=False):
            key = key[1:]
            if key not in self.Collection.keys():
                self.Collection[key] = None

    def Commit(self, wb, destroy=True):

        for keyval in self.Changed:
            item = self.Collection[keyval]
            if item:
                self.DB.put(self.Prefix + keyval, self.Collection[keyval].ToByteArray())
        for keyval in self.Deleted:
            self.DB.delete(self.Prefix + keyval)
            self.Collection[keyval] = None
        if destroy:
            self.Destroy()
        else:
            self.Changed = []
            self.Deleted = []

    def GetAndChange(self, keyval, new_instance=None, debug_item=False):

        item = self.TryGet(keyval)

        if item is None:
            if new_instance is None:
                item = self.ClassRef()
            else:
                item = new_instance

            self.Add(keyval, item)

        self.MarkChanged(keyval)

        return item

    def GetOrAdd(self, keyval, new_instance):

        item = new_instance

        if keyval in self.Deleted:
            self.Deleted.remove(keyval)

        self.Add(keyval, item)

        return item

    def GetItemBy(self, keyval):
        return self.GetAndChange(keyval)

    def TryGet(self, keyval):

        if keyval in self.Deleted:
            return None

        if keyval in self.Collection.keys():
            item = self.Collection[keyval]
            if item is None:
                item = self._GetItem(keyval)
            self.MarkChanged(keyval)
            return item

        # otherwise, chekc in the database
        key = self.DB.get(self.Prefix + keyval)

        # if the key is there, get the item
        if key is not None:

            self.MarkChanged(keyval)

            item = self._GetItem(keyval)

            return item

        return None

    def _GetItem(self, keyval):
        if keyval in self.Deleted:
            return None

        try:
            buffer = self.DB.get(self.Prefix + keyval)
            if buffer:
                item = self.ClassRef.DeserializeFromDB(binascii.unhexlify(buffer))
                self.Collection[keyval] = item
                return item
            return None
        except Exception as e:
            logger.error("Could not deserialize item from key %s : %s" % (keyval, e))

        return None

    def Add(self, keyval, item):
        self.Collection[keyval] = item
        self.MarkChanged(keyval)

    def Remove(self, keyval):
        if keyval not in self.Deleted:
            self.Deleted.append(keyval)

    def MarkChanged(self, keyval):
        if keyval not in self.Changed:
            self.Changed.append(keyval)

    # @TODO This has not been tested or verified to work.
    def Find(self, key_prefix):
        key_prefix = self.Prefix + key_prefix
        res = []
        for key, val in self.DB.iterator(prefix=key_prefix):
            res.append({key: val})
        return res

    def Destroy(self):
        self.DB = None
#        self.SN = None
        self.Collection = None
        self.ClassRef = None
        self.Prefix = None
        self.Deleted = None
        self.Changed = None
        logger = None
