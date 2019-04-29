import plyvel
import threading

from contextlib import contextmanager

from neo.Core.Blockchain import Blockchain
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Storage.Interface.DBInterface import DBProperties
from neo.logging import log_manager


logger = log_manager.getLogger()

"""
Description:
    All the methods are used within the dynamicallz generated class from the 
    database factory.
Usage:
    For a new database implementation all methods defined in 
    AbstractDBImplementation have to be implemented.
"""

# name of the init method for a generic database class
_init_method = '_db_init'

# name of the init method for a prefixed database class
_prefix_init_method = '_prefix_db_init'

# path where the data files are stored
_path = None

# either the real database class, in this case a LevelDB instance,
# or a prefixed db or snapshot
_db = None

# iterator instance created within openIter(self, properties)
_iter = None

# batch instance to perform batch operations on the database
_batch = None

_lock = threading.RLock()


@property
def Path(self):
    return self._path


def _prefix_db_init(self, _prefixdb):
    """
    init method used within the internalDBFactory, slightly different from the 
    init method as we don't have to open a new database but store a snapshot or
    a prefixed db.
    """

    try:
        self._db = _prefixdb
    except Exception as e:
        raise Exception("leveldb exception [ %s ]" % e)


def _db_init(self, path):
    """
    init method used within the DBFactory, opens a new or existing database.
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
    """

    # TODO check if snapshot db has to be closed
    from neo.Storage.Implementation.LevelDB.PrefixedDBFactory import internalDBFactory

    SnapshotDB = internalDBFactory('Snapshot')
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

    """

    self._iter = self._db.iterator(
        prefix=properties.prefix,
        include_value=properties.include_value,
        include_key=properties.include_key)

    yield self._iter
    self._iter.close()


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
    to implement an object that mimics a batches the behaviour.
    """

    with _lock:
        self._batch = self._db.write_batch()
        yield self._batch
        self._batch.write()


def getPrefixedDB(self, prefix):
    """
    Returns a prefixed db instance, which is basically the same as a real
    database but exists only in memory and contains only the data with the
    given prefix.

    A prefixed db is currently only used for the NotificationDB.

    If a database backend is implemented that does not support a prefixed
    database you have to implement a data structure/class that mimics its 
    behaviour.
    """

    # check if prefix db has to be closed
    from neo.Storage.Implementation.LevelDB.PrefixedDBFactory import internalDBFactory

    PrefixedDB = internalDBFactory('Prefixed')
    return PrefixedDB(self._db.prefixed_db(prefix))


def closeDB(self):
    self._db.close()
