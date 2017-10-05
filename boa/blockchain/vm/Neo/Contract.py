
class Contract():

    @property
    def Script(self):
        return GetScript(self)

    @property
    def StorageContext(self):
        return GetStorageContext(self)


def GetScript(contract):
    pass


def GetStorageContext(contract):
    pass


def Create(script,
           parameter_list,
           return_type,
           need_storage,
           version,
           author,
           email,
           description
           ):

    pass


def Migrate(script,
           parameter_list,
           return_type,
           need_storage,
           version,
           author,
           email,
           description
           ):

    pass

def Destroy(contract):
    pass


