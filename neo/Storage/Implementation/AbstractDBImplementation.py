from abc import ABC, abstractmethod
"""
Description:
    Alternative backends can be added by implementing the required methods
    of this abstract class.
Usage:
    The dynamically generated class coming from the database factory inherits
    from the abstract class, means the generated class cannot be used if not
    all methods defined in this class are overwritten.

    If this class is extended, make sure you extend also all other database
    implementations.

    For a more detailed description on the methods and how to implement a new
    database backend check out:
    neo.Storage.Implementation.LevelDB.LevelDBImpl
"""


class AbstractDBImplementation(ABC):

    @abstractmethod
    def __init__(self, path):
        """
        Init method used within the DBFactory, opens a new or existing database.

        Args:
            path (str): full path to the database directory.

        Attributes:
            path (str): full path to the database directory.
            _db (object): the database instance

        """
        raise NotImplementedError

    @abstractmethod
    def write(self, key, value):
        """
        Writes the given key/value pair to the database.

        Args:
            key (bytearray): has to be a prefixed bytearray, for prefixes check
                             neo.Storage.Common.DBPrefix

            value (bytearray): the value as bytearray

        Returns:
            None
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, key):
        """
        Retrieves the value based on the given key from the database.

        Args:
            key (bytearray): has to be a prefixed bytearray, for prefixes check
                             neo.Storage.Common.DBPrefix

        Returns:
            bytearray
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, key):
        """
        Deletes a row from the database.

        Args:
            key (bytearray): has to be a prefixed bytearray, for prefixes check
                             neo.Storage.Common.DBPrefix

        Returns:
            None
        """
        raise NotImplementedError

    @abstractmethod
    def cloneDatabaseStorage(self, clone_storage):
        """
        Clones the Smart Contract storages of the current database
        into "clone_storage"

        Args:
            clone_db (object): the instance of the database to clone to.

        Returns:
            clone_db (object): returns a cloned db instance

        """

        raise NotImplementedError

    @abstractmethod
    def createSnapshot(self):
        """
        Creates a read-only snapshot of the current database, used for
        DebugStorage and NotificationDB

        Args:
            None

        Returns:
            SnapshotDB (object): a new instance of a snapshot DB.

        """

        raise NotImplementedError

    @abstractmethod
    def openIter(self, properties):
        """
        Opens an iterator within a context manager.

        Usage:
            Due to the fact that a context manager is used the returned iterator has
            to be used within a with block. It's then closed after it returnes from
            the scope it's used in.
            Example from cloneDatabaseStorage method:

            with db_snapshot.openIter(DBProperties(prefix=DBPrefix.ST_Storage,
                                                   include_value=True)) as iterator:

        Args:
            properties (DBProperties): object containing the different properties
                                       used to open an iterator.

        Yields:
            _iter (LevelDB iterator): yields an iterator which is closed after the
                                      with block is done.
        """

        raise NotImplementedError

    @abstractmethod
    def getBatch(self):
        """
        Yields a batch instance which can be used to perform atomic updates on the
        database.
        As it's used within a context, getBatch has to called within a with block.

        Example:
        with self._db.getBatch() as batch:
            batch.put(b'key1', b'value')
            batch.put(b'key2', b'value')
            batch.delete(b'key2')

        If a database backend is implemented that does not support batches you have
        to implement an object that mimics batch behaviour.

        Args:
            None

        Yields:
            _batch (LevelDB batch): yields a new batch object which is processed after
                             the with block is done.
                LevelDB batch:
                    Methods:
                        put(key bytearry:, value: bytearray) -> None
                            Stores the given key/value pair to the database.

                        delete(key: bytearray) -> None
                            Deletes the given key from the database after
                            the batch was persisted.

                        clear(None) -> None
                            Removes all entries from a batch.


        """

        raise NotImplementedError

    @abstractmethod
    def getPrefixedDB(self, prefix):
        """
        Returns a prefixed db instance, which is basically the same as a real
        database but exists only in memory and contains only the data with the
        given prefix.

        A prefixed db is currently only used for the NotificationDB.

        If a database backend is implemented that does not support a prefixed
        database you have to implement a data structure/class that mimics its
        behaviour.

        Args:
            prefix (str): the prefix used to create a new prefixed DB.

        Returns:
            PrefixedDB (object): a new instance of a prefixed DB.
        """

        raise NotImplementedError

    @abstractmethod
    def closeDB(self):
        """Shuts down the database instance."""
        raise NotImplementedError
