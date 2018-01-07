from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Blockchain import GetBlockchain
import plyvel
from logzero import logger


class DebugStorage():

    __debug_storage_path = './Chains/debugstorage'
    __instance = None

    @property
    def db(self):
        return self._db

    def reset(self):
        for key in self._db.iterator(prefix=DBPrefix.ST_Storage, include_value=False):
            self._db.delete(key)

    def clone_from_live(self):
        print("cloining from live!")
        clone_db = GetBlockchain()._db.snapshot()
        for key, value in clone_db.iterator(prefix=DBPrefix.ST_Storage, include_value=True):
            self._db.put(key, value)
        print("cloned db")

    def __init__(self):

        try:
            self._db = plyvel.DB(self.__debug_storage_path, create_if_missing=True)
            print("created begustorage")
        except Exception as e:
            logger.info("DEBUG leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('DEBUG Leveldb Unavailable %s ' % e)

    @staticmethod
    def instance():
        if not DebugStorage.__instance:
            print("creating instance!")
            DebugStorage.__instance = DebugStorage()
            DebugStorage.__instance.clone_from_live()
        return DebugStorage.__instance
