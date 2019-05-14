import plyvel
import threading

from contextlib import contextmanager

from neo.Storage.Implementation.AbstractDBImplementation import (
    AbstractDBImplementation
)
from neo.Utils.plugin import load_class_from_path
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Storage.Interface.DBInterface import DBProperties
from neo.logging import log_manager


logger = log_manager.getLogger()

"""
Description:
    Backend implementation for the LevelDB database.
    It overrides all methods from the `AbstractDBImplementation` class.
    The database factory (`DBFactory`) uses these methods to dynamically
    generate a conforming database instance for internal usage.

Usage:
    For a new database implementation all methods defined in
    AbstractDBImplementation have to be implemented.

"""


class LevelDBImpl(AbstractDBImplementation):

    # the instance of the database
    _db = None

    _lock = threading.RLock()

    def __init__(self, path):

        """
        Init method used within the DBFactory, opens a new or existing database.

        Args:
            path (str): full path to the database directory.

        Attributes:
            path (str): full path to the database directory.
            _db (object): the database instance

        """

        try:
            self._path = path
            self._db = plyvel.DB(path, create_if_missing=True)
            logger.info("Created DB at %s " % self._path)
        except Exception as e:
            raise Exception("leveldb exception [ %s ]" % e)

    def write(self, key, value):
        self._db.put(key, value)

    def get(self, key, default=None):
        return self._db.get(key, default)

    def delete(self, key):
        self._db.delete(key)

    def cloneDatabase(self, clone_db):
        """
        Clones the current database into "clone_db"

        Args:
            clone_db (object): the instance of the database to clone to.

        Returns:
            clone_db (object): returns a cloned db instance

        """

        db_snapshot = self.createSnapshot()
        with db_snapshot.openIter(DBProperties(prefix=DBPrefix.ST_Storage,
                                               include_value=True)) as iterator:
            for key, value in iterator:
                clone_db.write(key, value)
        return clone_db

    def createSnapshot(self):
        """
        Creates a snapshot of the current database, used for DebugStorage and
        NotificationDB. To keep the snapshot compatible to the current design it's
        created through a factory which returns basically the same class we use
        for the real database and all the methods that can be used on the real db
        can also be used on the snapshot.

        Args:
            None

        Returns:
            SnapshotDB (object): a new instance of a snapshot DB.

        """

        SnapshotDB = load_class_from_path('neo.Storage.Implementation.LevelDB.LevelDBSnapshot.LevelDBSnapshot')
        return SnapshotDB(self._db.snapshot())

    @contextmanager
    def openIter(self, properties):
        """
        Opens an iterator within a context manager.

        Usage:
            Due to the fact that a context manager is used the returned iterator has
            to be used within a with block. It's then closed after it returnes from
            the scope it's used in.
            Example from cloneDatabase method:

            with db_snapshot.openIter(DBProperties(prefix=DBPrefix.ST_Storage,
                                                   include_value=True)) as iterator:

        Args:
            properties (DBProperties): object containing the different properties
                                       used to open an iterator.

        Yields:
            _iter (LevelDB iterator): yields an iterator which is closed after the
                                      with block is done.
        """

        _iter = self._db.iterator(
            prefix=properties.prefix,
            include_value=properties.include_value,
            include_key=properties.include_key)

        yield _iter
        _iter.close()

    @contextmanager
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

        """

        with self._lock:
            _batch = self._db.write_batch()
            yield _batch
            _batch.write()

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

        PrefixedDB = load_class_from_path('neo.Storage.Implementation.LevelDB.LevelDBSnapshot.LevelDBSnapshot')
        return PrefixedDB(self._db.prefixed_db(prefix))

    def closeDB(self):
        self._db.close()
