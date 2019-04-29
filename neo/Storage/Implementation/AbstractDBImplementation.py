from abc import ABC, abstractmethod
"""
Description:
    Abstract class used to ensure the mandatory methods are overwritten
    in everxy new database implementation.
Usage:
    The dynamically generated class coming from the database factory inherits
    from the abstract class, means the generated class cannot be used if not 
    all methods defined in this class are overwritten.

    If this class is extended, make sure you extend also all other database
    implementations.

    For a more detailed information on the methods and how to implement a new 
    database backend check out:
    neo.Storage.Implementation.LevelDB.LevelDBClassMethods
"""


class AbstractDBImplementation(ABC):

    @abstractmethod
    def write(self, key, value):
        raise NotImplementedError

    @abstractmethod
    def get(self, key):
        raise NotImplementedError

    @abstractmethod
    def delete(self, key):
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

    @abstractmethod
    def getPrefixedDB(self, prefix):
        raise NotImplementedError
