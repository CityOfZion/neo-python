
from peewee import *
from neo.Defaults import PEEWEE_DB



class PWDatabase(object):


    __instance__ = None

    _db = None

    def __init__(self):
        self._db = SqliteDatabase(PEEWEE_DB)
        self.startup()


    def close(self):
        self._db.close()
        self._db = None

    def startup(self):
        self._db.connect()

    @property
    def DB(self):
        return self._db

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
            PWDatabase.__instance__.close()
        PWDatabase.__instance__ = None