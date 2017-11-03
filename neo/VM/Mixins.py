
class EquatableMixin():

    def Equals(self, other):
        pass


class InteropMixin():
    pass


class ScriptTableMixin():

    def GetScript(self, script_hash):
        pass


class ScriptContainerMixin(InteropMixin):

    def GetMessage(self):
        pass


class CryptoMixin():

    def Hash160(self, message):
        pass

    def Hash256(self, message):
        pass

    def VerifySignature(self, message, signature, pubkey):
        pass
