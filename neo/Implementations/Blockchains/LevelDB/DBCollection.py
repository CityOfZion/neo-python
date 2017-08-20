import binascii
from autologging import logged
from neo.UInt256 import UInt256
from neo.UInt160 import UInt160
from neo.Core.State.ValidatorState import ValidatorState
@logged
class DBCollection():

    DB=None
    SN=None
    Prefix=None

    ClassRef = None

    Collection = {}

    Changed = []
    Deleted = []

    Debug = False


    def __init__(self, db, sn, prefix, class_ref, debug=False):

        self.DB = db
        self.SN = sn

        self.Prefix = prefix

        self.ClassRef = class_ref
        self.Debug = debug

        self.Collection = {}
        self.Changed = []
        self.Deleted = []

        self._BuildCollection()

    def _BuildCollection(self):

        for key, buffer in self.SN.iterator(prefix=self.Prefix):
            key = key[1:]
            try:
                self.Collection[key] = self.ClassRef.DeserializeFromDB( binascii.unhexlify( buffer))
            except Exception as e:
                print("could not decode class %s %s %s %s" % (self.ClassRef,key, buffer, e))



    def Commit(self, wb, destroy=True):
        try:

            for item in self.Changed:
                wb.put( self.Prefix + item, self.Collection[item].ToByteArray() )
            for item in self.Deleted:
                wb.delete(self.Prefix + item)
            if destroy:
                self.Destroy()
            else:
                self.Changed = []
                self.Deleted = []
        except Exception as e:
            print("COULD NOT COMMIT: %s %s %s" % (e, self.ClassRef, item))

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

        self.Add(keyval,item)

        return item

    def GetItemBy(self, keyval):
        return self.GetAndChange(keyval)


    def TryGet(self, keyval):
        if keyval in self.Collection:
            self.MarkChanged(keyval)
            return self.Collection[keyval]
        return None

    def Add(self, keyval, item):
        self.Collection[keyval] = item
        self.MarkChanged(keyval)

    def Remove(self, keyval):
        if not keyval in self.Deleted:
            self.Deleted.append(keyval)

    def MarkChanged(self, keyval):
        if not keyval in self.Changed:
            self.Changed.append(keyval)


    def Destroy(self):
        self.DB = None
        self.SN = None
        self.Collection = None
        self.ClassRef = None
        self.Prefix = None
        self.Deleted = None
        self.Changed = None
        self.__log = None