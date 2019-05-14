from neo.Storage.Implementation.LevelDB.LevelDBImpl import LevelDBImpl


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
