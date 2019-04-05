import plyvel
from neo.logging import log_manager

logger = log_manager.getLogger('LevelDB')

"""Document me"""

_init_method = '_db_init'

_path = None

_db = None

_iter = None

_snapshot = None

_batch = None


@property
def Path(self):
    return self._path


def _db_init(self, path):
    try:
        self._path = path
        print('path:::: ', path)
        self._db = plyvel.DB(path, create_if_missing=True)
        logger.info("Created Blockchain DB at %s " % self._path)
    except Exception as e:
        raise Exception("leveldb exception [ %s ]" % e)


def write(self, key, value):
    self._db.put(key, value)


def writeBatch(self, batch: dict):
    with self._db.write_batch() as wb:
        for key, value in batch.items():
            wb.put(key, value)


def get(self, key, default=None):
    _value = self._db.get(key, default)
    return _value


def delete(self, key):
    self._db.delete(key)


def deleteBatch(self, batch: dict):
    with self._db.write_batch() as wb:
        for key in batch:
            wb.delete(key)


def createSnapshot(self):
    self._snapshot = self._db.snapshot()
    return self._snapshot


def dropSnapshot(self):
    self._snapshot.close()
    self._snapshot = None


def openIter(self, properties, start=None, end=None):
    # TODO start implement start and end

    self._iter = self._db.iterator(
                                    properties.prefix,
                                    properties.include_value)
    return self._iter


def getBatch(self):
    self._batch = self._db.write_batch()


def dropBatch(self):
    self._batch = None


def closeIter(self):
    self._iter.close()
    self._iter = None


def closeDB(self):
    self._db.close()
