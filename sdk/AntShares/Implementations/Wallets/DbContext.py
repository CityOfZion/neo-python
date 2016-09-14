#!/usr/bin/env python

import pymongo
import json

class Mongodb(object):
    def __init__(self,host,port):
        self.db = pymongo.MongoClient(host, port).ecredits

    def getCol(self, col_name):
        return self.db.__getattr__(col_name)

    def replace(self, col, key, item):
        if not isinstance(item, dict):
            return False
        collection = self.getCol(col)
        try:
            collection.update(key, dict(item),upsert=True)
            return True
        except Exception as e:
            print e
            return False

    def update(self, col, key, item,):
        collection = self.getCol(col)
        try:
            collection.update(key, dict(item))
            return True
        except Exception as e:
            print e
            return False

    def read(self, col, key, item={'_id':0}):
        collection = self.getCol(col)
        result = collection.find(key, dict(item))
        if result.count() == 0:
            return []
        return [r for r in result]

def __test():
    mongo = Mongodb(config.bcdb.host,config.bcdb.port)
    qry = {'txid':'123456','idx':0}
    item = {'txid':'123456','idx':0, 'value':100,'status':0}
    mongo.replace(qry,item,'test')
    item = {'$set':{'value':200}}
    mongo.update(qry,item,'test')
    print mongo.read('test',qry)

if __name__ == '__main__':
    import config
    __test()
