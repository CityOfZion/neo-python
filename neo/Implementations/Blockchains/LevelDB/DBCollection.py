import binascii
from neo.SmartContract.Iterable import EnumeratorBase
from neo.logging import log_manager

logger = log_manager.getLogger('db')


class DBCollection:
    DB = None
    Prefix = None

    ClassRef = None

    Collection = {}

    Changed = []
    Deleted = []

    _built_keys = False

    DebugStorage = False

    _ChangedResetState = None
    _DeletedResetState = None

    def __init__(self, db, prefix, class_ref):

        self.DB = db

        self.Prefix = prefix

        self.ClassRef = class_ref

        self.Collection = {}
        self.Changed = []
        self.Deleted = []

        self._ChangedResetState = None
        self._DeletedResetState = None

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
                if not wb:
                    self.DB.put(self.Prefix + keyval, self.Collection[keyval].ToByteArray())
                else:
                    wb.put(self.Prefix + keyval, self.Collection[keyval].ToByteArray())
        for keyval in self.Deleted:
            if not wb:
                self.DB.delete(self.Prefix + keyval)
            else:
                wb.delete(self.Prefix + keyval)
            self.Collection[keyval] = None
        if destroy:
            self.Destroy()
        else:
            self.Changed = []
            self.Deleted = []
            self._ChangedResetState = None
            self._DeletedResetState = None

    def Reset(self):
        self.Changed = self._ChangedResetState
        self.Deleted = self._DeletedResetState

        self._ChangedResetState = None
        self._DeletedResetState = None

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

    def ReplaceOrAdd(self, keyval, new_instance):

        item = new_instance

        if keyval in self.Deleted:
            self.Deleted.remove(keyval)

        self.Add(keyval, item)

        return item

    def GetOrAdd(self, keyval, new_instance):

        existing = self.TryGet(keyval)

        if existing:
            return existing

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

    def MarkForReset(self):
        self._ChangedResetState = self.Changed
        self._DeletedResetState = self.Deleted

    def MarkChanged(self, keyval):
        if keyval not in self.Changed:
            self.Changed.append(keyval)

    def TryFind(self, key_prefix):
        candidates = {}
        for keyval in self.Collection.keys():
            # See if we find a partial match in the keys that not have been committed yet, excluding those that are to be deleted
            if key_prefix in keyval and keyval not in self.Deleted:
                candidates[keyval[20:]] = self.Collection[keyval].Value

        db_results = self.Find(key_prefix)

        # {**x, **y} merges two dictionaries, with the values of y overwriting the vals of x
        # withouth this merge, you sometimes get 2 results for each key
        # then take the dict and make a list of tuples
        final_collection = [(k, v) for k, v in {**db_results, **candidates}.items()]

        return EnumeratorBase(iter(final_collection))

    def Find(self, key_prefix):
        key_prefix = self.Prefix + key_prefix
        res = {}
        for key, val in self.DB.iterator(prefix=key_prefix):
            # we want the storage item, not the raw bytes
            item = self.ClassRef.DeserializeFromDB(binascii.unhexlify(val)).Value
            # also here we need to skip the 1 byte storage prefix
            res_key = key[21:]
            res[res_key] = item
        return res

    def Destroy(self):
        self.DB = None
        self.Collection = None
        self.ClassRef = None
        self.Prefix = None
        self.Deleted = None
        self.Changed = None
        self._ChangedResetState = None
        self._DeletedResetState = None
        logger = None
