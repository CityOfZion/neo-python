import logging
from peewee import Proxy, SqliteDatabase
from neo.logging import log_manager

logger = log_manager.getLogger('peewee')
log_manager.config_stdio([('peewee', logging.ERROR)])


class PWDatabase:
    __proxy = None

    @staticmethod
    def DBProxy():
        if not PWDatabase.__proxy:
            PWDatabase.__proxy = Proxy()
        return PWDatabase.__proxy

    _db = None

    def __init__(self, path):
        try:
            self._db = SqliteDatabase(path, check_same_thread=False)
            PWDatabase.DBProxy().initialize(self._db)
            self.startup()
        except Exception as e:
            logger.error("database file does not exist, or incorrect permissions")

    def close(self):
        self._db.close()
        self._db = None

    def startup(self):
        self._db.connect()

    @property
    def DB(self):
        return self._db
