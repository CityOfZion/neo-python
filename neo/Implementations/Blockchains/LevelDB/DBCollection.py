from neo.Core.State.AccountState import AccountState
import binascii
from autologging import logged

@logged
class DBCollection():

    DB=None
    Prefix=None

    ClassRef = None

    Collection = {}

    Changed = []
    Deleted = []

    def __init__(self, db, prefix, class_ref):

        self.DB = db
        self.Prefix = prefix

        self.ClassRef = class_ref

        self.Collection = {}
        self.Changed = []
        self.Deleted = []

        self._BuildCollection()

    def _BuildCollection(self):

        for key, buffer in self.DB.iterator(prefix=self.Prefix):
            self.Collection[key] = self.ClassRef.DeserializeFromDB( binascii.unhexlify( buffer))

    def Commit(self, wb):
        for item in self.Changed:
#            print("committing item %s %s" % (item, type(item)))
            wb.put( self.Prefix + item, self.Collection[item].ToByteArray() )
        for item in self.Deleted:
            wb.delete(self.Prefix + item)


    def GetAndChange(self, keyval, new_instance=None):

        item = self.TryGet(keyval)

        if item is None:

            if new_instance is None:
                item = self.ClassRef()
            else:
                item = new_instance

            self.Add(keyval, item)

        self.MarkChanged(keyval)

        return item



    def GetItemBy(self, keyval):
        return self.GetAndChange(keyval)


    def TryGet(self, keyval):
        if keyval in self.Collection:
            self.MarkChanged(keyval)
            return self.Collection[keyval]
        return None

    def Add(self, keyval, item):
        self.MarkChanged(keyval)
        self.Collection[keyval] = item


    def Remove(self, keyval):
        if not keyval in self.Deleted:
            self.Deleted.append(keyval)

    def MarkChanged(self, keyval):
        if not keyval in self.Changed:
            self.Changed.append(keyval)
