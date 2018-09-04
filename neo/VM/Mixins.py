from abc import ABC, abstractmethod


class EquatableMixin(ABC):

    @abstractmethod
    def Equals(self, other):
        pass


class InteropMixin:
    pass


class ScriptTableMixin(ABC):

    @abstractmethod
    def GetScript(self, script_hash):
        pass


class ScriptContainerMixin(ABC, InteropMixin):

    @abstractmethod
    def GetMessage(self):
        pass


class CryptoMixin(ABC):

    @abstractmethod
    def Hash160(self, message):
        pass

    @abstractmethod
    def Hash256(self, message):
        pass

    @abstractmethod
    def VerifySignature(self, message, signature, pubkey):
        pass
