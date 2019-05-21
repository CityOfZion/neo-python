import plyvel
import threading

from contextlib import contextmanager

from neo.Storage.Implementation.AbstractDBImplementation import (
    AbstractDBImplementation
)
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

    def cloneDatabaseStorage(self, clone_storage):
        db_snapshot = self.createSnapshot()
        with db_snapshot.openIter(DBProperties(prefix=DBPrefix.ST_Storage,
                                               include_value=True)) as iterator:
            for key, value in iterator:
                clone_storage.write(key, value)
        return clone_storage

    def createSnapshot(self):
        return LevelDBSnapshot(self._db.snapshot())

    @contextmanager
    def openIter(self, properties):
        _iter = self._db.iterator(
            prefix=properties.prefix,
            include_value=properties.include_value,
            include_key=properties.include_key)

        yield _iter
        _iter.close()

    @contextmanager
    def getBatch(self):

        with self._lock:
            _batch = self._db.write_batch()
            yield _batch
            _batch.write()

    def getPrefixedDB(self, prefix):
        return LevelDBSnapshot(self._db.prefixed_db(prefix))

    def closeDB(self):
        self._db.close()


class LevelDBSnapshot(LevelDBImpl):

    def __init__(self, _prefixdb):
        """
        Init method used with a snapshotDB or prefixedDB, slightly different from the
        init method as we don't have to open a new database but store a snapshot or
        a prefixed db.

        Args:
            _prefixdb (object): the prefixed db instance

        """

        try:
            self._db = _prefixdb
        except Exception as e:
            raise Exception("leveldb exception [ %s ]" % e)
