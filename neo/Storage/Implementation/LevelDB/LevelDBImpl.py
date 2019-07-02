import plyvel
import threading


from contextlib import contextmanager

from neo.Storage.Implementation.AbstractDBImplementation import (
    AbstractDBImplementation
)
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Storage.Interface.DBProperties import DBProperties
import neo.Storage.Implementation.LevelDB.LevelDBSnapshot
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
            self._db = plyvel.DB(self._path, create_if_missing=True,
                                 max_open_files=100,
                                 lru_cache_size=10 * 1024 * 1024)
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
        with db_snapshot.db.openIter(DBProperties(prefix=DBPrefix.ST_Storage, include_value=True)) as iterator:
            for key, value in iterator:
                clone_storage.write(key, value)
        return clone_storage

    def createSnapshot(self):
        return neo.Storage.Implementation.LevelDB.LevelDBSnapshot.LevelDBSnapshot(self)

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
        return PrefixedLevelDBImpl(self._db.prefixed_db(prefix))

    def closeDB(self):
        self._db.close()


class PrefixedLevelDBImpl(LevelDBImpl):
    def __init__(self, prefixed_db):
        self._db = prefixed_db
