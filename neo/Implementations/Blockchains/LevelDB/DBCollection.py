import binascii
from autologging import logged
from neo.UInt256 import UInt256
from neo.UInt160 import UInt160
from neo.Core.State.ValidatorState import ValidatorState
import inspect

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


    _built_keys=False


    def __init__(self, db, sn, prefix, class_ref, debug=False):

        self.DB = db
        self.SN = sn

        self.Prefix = prefix

        self.ClassRef = class_ref
        self.Debug = debug

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
            for key,val in self.Collection.items():
                if val is not None:
                    ret[key] = val
            return ret
        except Exception as e:
            print("error getting items %s " % e)

        return {}

    def _BuildCollectionKeys(self):
        for key in self.SN.iterator(prefix=self.Prefix, include_value=False):
            key = key[1:]
            if not key in self.Collection.keys():
                self.Collection[key] = None

    def Commit(self, wb, destroy=True):
        try:

            for keyval in self.Changed:
                item = self.Collection[keyval]
                if item is None:
                    print("key %s %s " % (keyval, self.Collection[keyval]))
                    print("THIS IS BAD %s " % self.Collection.items())
                    raise Exception("ITEM NONONEEEE %s " % keyval)
                else:
                    wb.put( self.Prefix + keyval, self.Collection[keyval].ToByteArray() )
            for keyval in self.Deleted:
                wb.delete(self.Prefix + keyval)
            if destroy:
                self.Destroy()
            else:
                self.Changed = []
                self.Deleted = []
        except Exception as e:
            print("COULD NOT COMMIT %s %s " % (e, self.ClassRef))
            (frame, filename, line_number,
             function_name, lines, index) = inspect.getouterframes(inspect.currentframe())[1]
            print(frame, filename, line_number, function_name, lines, index)
            raise Exception("BAD")


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

        #if the item has been looked up, or added it will be in Keys
        if keyval in self.Collection.keys():
            item = self.Collection[keyval]
            if item is None:
                item = self._GetItem(keyval)
            self.MarkChanged(keyval)
            return item

        #otherwise, chekc in the database
        key= self.SN.get(self.Prefix + keyval)

        #if the key is there, get the item
        if key is not None:

            self.MarkChanged(keyval)

            item = self._GetItem(keyval)

            return item

        return None


    def _GetItem(self, keyval):
        try:
            buffer = self.SN.get(self.Prefix + keyval)
            item = self.ClassRef.DeserializeFromDB(binascii.unhexlify(buffer))
            self.Collection[keyval] = item
            return item
        except Exception as e:
            print("Could not deserialize item from key %s : %s" % (keyval, e))

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