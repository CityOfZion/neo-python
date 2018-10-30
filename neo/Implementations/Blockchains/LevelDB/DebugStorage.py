from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Blockchain import GetBlockchain
import plyvel
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger('db')


class DebugStorage:
    __instance = None

    @property
    def db(self):
        return self._db

    def reset(self):
        for key in self._db.iterator(prefix=DBPrefix.ST_Storage, include_value=False):
            self._db.delete(key)

    def clone_from_live(self):
        clone_db = GetBlockchain()._db.snapshot()
        for key, value in clone_db.iterator(prefix=DBPrefix.ST_Storage, include_value=True):
            self._db.put(key, value)

    def __init__(self):

        try:
            self._db = plyvel.DB(settings.debug_storage_leveldb_path, create_if_missing=True)
        except Exception as e:
            logger.info("DEBUG leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('DEBUG Leveldb Unavailable %s ' % e)

    @staticmethod
    def instance():
        if not DebugStorage.__instance:
            DebugStorage.__instance = DebugStorage()
            DebugStorage.__instance.clone_from_live()
        return DebugStorage.__instance
