from neo.Storage.Implementation.DBFactory import getBlockchainDB
from neo.Settings import settings
from collections import abc
from unittest import TestCase, skip
import shutil
import os


class LevelDBTest(TestCase):

    DB_TESTPATH = os.path.join(settings.DATA_DIR_PATH, 'UnitTestChain')
    _db = None

    @classmethod
    def setUpClass(cls):
        settings.setup_unittest_net()
        cls._db = getBlockchainDB(cls.DB_TESTPATH)

    @classmethod
    def tearDownClass(cls):
        cls._db.closeDB()
        shutil.rmtree(cls.DB_TESTPATH)

    def setupDB(self, db):
        if self._db:
            self._db.closeDB()
            shutil.rmtree(self.DB_TESTPATH)

        self._db = getBlockchainDB(self.DB_TESTPATH)

    def test_write_read(self):

        self._db.write(b'00001.x', b'x')
        self._db.write(b'00001.y', b'y')
        self._db.write(b'00001.z', b'z')

        self.assertEqual(self._db.get(b'00001.x'), b'x')
        self.assertEqual(self._db.get(b'00001.y'), b'y')
        self.assertEqual(self._db.get(b'00001.z'), b'z')

    def test_delete_default(self):

        self._db.write(b'00001.x', b'x')
        self._db.delete(b'00001.z')

        self.assertEqual(self._db.get(b'00001.z'), None)
        self.assertEqual(self._db.get(b'00001.z', b'default'), b'default')

    def test_iterator(self):

        self._db.write(b'00001.x', b'x')
        self._db.write(b'00001.y', b'y')
        self._db.write(b'00001.z', b'z')

        self._db.write(b'00002.w', b'w')
        self._db.write(b'00002.x', b'x')
        self._db.write(b'00002.y', b'y')
        self._db.write(b'00002.z', b'z')

        from neo.Storage.Interface.DBInterface import DBProperties

        '''
            Hhas to be converted as leveldb returns a custom iterator object, 
            rocksdb just uses lists/dicts. Should not matter, still tests the 
            same.
        '''
        def make_compatible(obj, to):
            if not isinstance(obj, to):
                new_obj = to(obj)
                if isinstance(new_obj, dict):
                    return new_obj.items()
                return new_obj
            return obj

        with self._db.openIter(DBProperties(prefix=b'00001', include_value=True, include_key=False)) as iterator:

            iterator = make_compatible(iterator, list)
            self.assertEqual(len(iterator), 3)
            self.assertIsInstance(iterator, list)

        with self._db.openIter(DBProperties(prefix=b'00002', include_value=False, include_key=True)) as iterator:
            iterator = make_compatible(iterator, list)
            self.assertEqual(len(iterator), 4)
            self.assertIsInstance(iterator, list)

        with self._db.openIter(DBProperties(prefix=b'00002', include_value=True, include_key=True)) as iterator:
            iterator = make_compatible(iterator, dict)
            self.assertEqual(len(iterator), 4)
            self.assertIsInstance(iterator, abc.ItemsView)

        with self._db.openIter(DBProperties(prefix=None, include_value=True, include_key=True)) as iterator:
            iterator = make_compatible(iterator, dict)
            self.assertEqual(len(iterator), 7)
            self.assertIsInstance(iterator, abc.ItemsView)

        with self._db.openIter(DBProperties(prefix=None, include_value=False, include_key=True)) as iterator:
            iterator = make_compatible(iterator, list)
            self.assertEqual(len(iterator), 7)
            self.assertIsInstance(iterator, list)

        with self._db.openIter(DBProperties(prefix=None, include_value=True, include_key=False)) as iterator:
            iterator = make_compatible(iterator, list)
            self.assertEqual(len(iterator), 7)
            self.assertIsInstance(iterator, list)

    def test_batch(self):

        self._db.write(b'00001.x', b'x')
        self._db.write(b'00001.y', b'y')
        self._db.write(b'00001.z', b'z')

        self._db.write(b'00002.w', b'w')
        self._db.write(b'00002.x', b'x')
        self._db.write(b'00002.y', b'y')
        self._db.write(b'00002.z', b'z')

        from neo.Storage.Interface.DBInterface import DBProperties

        with self._db.getBatch() as batch:
            batch.put(b'00001.x', b'batch_x')
            batch.delete(b'00002.x')

        self.assertEqual(self._db.get(b'00001.x'), b'batch_x')
        self.assertIsNone(self._db.get(b'00002.x'))
