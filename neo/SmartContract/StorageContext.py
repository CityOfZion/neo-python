from neo.VM.Mixins import InteropMixin


class StorageContext(InteropMixin):

    ScriptHash = None
    IsReadOnly = False

    def __init__(self, script_hash, read_only=False):

        self.ScriptHash = script_hash
        self.IsReadOnly = read_only

    def ToArray(self):
        # hmmm... script hashes are already a byte array at the moment, i think?
        # return self.ScriptHash.ToArray()
        return self.ScriptHash
