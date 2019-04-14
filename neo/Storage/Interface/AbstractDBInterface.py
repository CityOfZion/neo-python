from abc import ABC, abstractmethod


class AbstractDBInterface(ABC):

    @abstractmethod
    def write(self, key, value):
        raise NotImplementedError

    @abstractmethod
    def writeBatch(self, batch):
        raise NotImplementedError

    @abstractmethod
    def get(self, key):
        raise NotImplementedError

    @abstractmethod
    def delete(self, key):
        raise NotImplementedError

    @abstractmethod
    def deleteBatch(self, batch: dict):
        raise NotImplementedError

    @abstractmethod
    def cloneDatabase(self, clone_db):
        raise NotImplementedError

    @abstractmethod
    def createSnapshot(self):
        raise NotImplementedError

    @abstractmethod
    def openIter(self, properties):
        raise NotImplementedError

    @abstractmethod
    def getBatch(self):
        raise NotImplementedError

    @abstractmethod
    def closeDB(self):
        raise NotImplementedError
