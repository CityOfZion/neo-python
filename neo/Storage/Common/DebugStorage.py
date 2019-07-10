from neo.Blockchain import GetBlockchain
from neo.Storage.Common.DBPrefix import DBPrefix
import neo.Storage.Implementation.DBFactory as DBFactory
from neo.Storage.Interface.DBProperties import DBProperties
from neo.logging import log_manager

logger = log_manager.getLogger('db')


class DebugStorage:
    __instance = None

    @property
    def db(self):
        return self._db

    def reset(self):
        with self._db.openIter(
                DBProperties(prefix=DBPrefix.ST_Storage,
                             include_value=False)) as it:
            for key in it:
                self._db.delete(key)

    def __init__(self):

        try:
            self._db = GetBlockchain().Default().GetDB().cloneDatabaseStorage(
                DBFactory.getDebugStorageDB())
        except Exception as e:
            logger.info("DEBUG leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('DEBUG Leveldb Unavailable %s ' % e)

    @staticmethod
    def instance():
        if not DebugStorage.__instance:
            DebugStorage.__instance = DebugStorage()
        return DebugStorage.__instance
