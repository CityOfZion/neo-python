class Script:
    def __init__(self, crypto, script):
        self._crypto = crypto
        self._value = script
        self._script_hash = None

    @property
    def ScriptHash(self) -> bytearray:
        if self._script_hash is None:
            self._script_hash = self._crypto.Hash160(self._value)
        return self._script_hash

    @property
    def Length(self) -> int:
        return len(self._value)

    def __call__(self, *args, **kwargs):
        index = args[0]
        return self._value[index]

    def __getitem__(self, item):
        return self._value[item]

    @classmethod
    def FromHash(cls, scrip_hash, script):
        o = cls(None, script)
        o._script_hash = scrip_hash
        return o
