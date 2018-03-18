from abc import ABC, abstractmethod
from neo.VM.Mixins import InteropMixin
from neo.VM.InteropService import StackItem


class Iterator(ABC, InteropMixin):
    @abstractmethod
    def Dispose(self) -> None:
        pass

    @abstractmethod
    def Key(self) -> StackItem:
        pass

    @abstractmethod
    def Next(self) -> bool:
        pass

    @abstractmethod
    def Value(self) -> StackItem:
        pass
