import logging
from peewee import *
from logzero import logger

logger = logging.getLogger('peewee')
logger.setLevel(logging.ERROR)


class PWDatabase(object):

    __proxy = None

    @staticmethod
    def DBProxy():
        if not PWDatabase.__proxy:
            PWDatabase.__proxy = Proxy()
        return PWDatabase.__proxy

    __instance__ = None
    __dbpath__ = 'accounts.db3'

    _db = None

    def __init__(self):
        try:
            self._db = SqliteDatabase(PWDatabase.__dbpath__, check_same_thread=False)
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

    @staticmethod
    def Initialize(path=None):
        if path is not None:
            PWDatabase.__dbpath__ = path

    @staticmethod
    def Context():
        if not PWDatabase.__instance__:
            PWDatabase.__instance__ = PWDatabase()
        return PWDatabase.__instance__

    @staticmethod
    def ContextDB():
        return PWDatabase.Context().DB

    @staticmethod
    def Destroy():
        if PWDatabase.__instance__:
            try:
                PWDatabase.__instance__.close()
            except Exception as e:
                pass
        PWDatabase.__instance__ = None
