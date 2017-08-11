

class DBCollection():

    DB=None
    Prefix=None

    ClassRef = None

    Collection = {}

    def __init__(self, db, prefix, class_ref):

        self.DB = db
        self.Prefix = prefix

        self.ClassRef = class_ref

        self._BuildCollection()

    def _BuildCollection(self):

        for key, buffer in self.DB.iterator(prefix=self.Prefix):
            self.Collection[key] = self.ClassRef.DeserializeFromDB(buffer)


    def GetAndChange(self, itemval, new_instance=None):
        item = None
        try:
            item = self.Collection[itemval]
        except Exception as e:
            print("item not found %s " % e)

        if item is None:

            if new_instance is not None:
                item = self.ClassRef()
            else:
                item = new_instance

            self.Add(itemval, item)

        return item



    def GetItemBy(self, itemval):
        return self.GetAndChange(itemval)


    def TryGet(self, itemval):
        if itemval in self.Collection:
            return self.Collection[itemval]
        return None

    def Add(self, keyval, item):
        self.Collection[keyval] = item

