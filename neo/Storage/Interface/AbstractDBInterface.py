from abc import ABC, abstractmethod


class AbstractDBInterface(ABC):

    @abstractmethod
    def write(self, key, value): raise NotImplementedError

    @abstractmethod
    def writeBatch(self, batch): raise NotImplementedError

    @abstractmethod
    def get(self, key): raise NotImplementedError

    @abstractmethod
    def createSnapshot(self): raise NotImplementedError

    @abstractmethod
    def dropSnapshot(self, snapshot): raise NotImplementedError

    @abstractmethod
    def openIter(self, properties, start=None, end=None): raise NotImplementedError

    @abstractmethod
    def closeIter(self): raise NotImplementedError
