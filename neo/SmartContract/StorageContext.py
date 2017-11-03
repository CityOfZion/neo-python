from neo.VM.Mixins import InteropMixin


class StorageContext(InteropMixin):

    ScriptHash = None

    def __init__(self, script_hash):

        self.ScriptHash = script_hash

    def ToArray(self):
        # hmmm... script hashes are already a byte array at the moment, i think?
        # return self.ScriptHash.ToArray()
        return self.ScriptHash
