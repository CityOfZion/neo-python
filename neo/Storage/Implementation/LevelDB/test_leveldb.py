from neo.Storage.Implementation.LevelDB.LevelDBImpl import LevelDBImpl

db = LevelDBImpl(b"/home/enzensbe/source/neo-python/neo/Storage/Implementation/LevelDB/1")
print(db)
db2 = LevelDBImpl(b"/home/enzensbe/source/neo-python/neo/Storage/Implementation/LevelDB/2")
print(db2)
db3 = LevelDBImpl(b"/home/enzensbe/source/neo-python/neo/Storage/Implementation/LevelDB/2")
print(db3)
