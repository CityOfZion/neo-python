from neo.Storage.Interface.AbstractDBInterface import AbstractDBInterface
from neo.Settings import settings
from neo.logging import log_manager


"""Module is used to access the different databases.
Import the module and use the getters to  access the different databases.
Configuration is done in neo.Settings.DATABASE_PROPS dict.
"""

logger = log_manager.getLogger('DBFactory')

BC_CONST = 'blockchain'
NOTIF_CONST = 'notification'
DEBUG_CONST = 'debug'

print('props ', settings.database_properties())
DATABASE_PROPS = settings.database_properties()

_blockchain_db_instance = None

_notif_db_instance = None

_debug_db_instance = None


def getBlockchainDB():
    return _blockchain_db_instance


def getNotificationDB():
    return _notif_db_instance


def getDebugStorageDB():
    return _debug_db_instance


def _dbFactory(dbType, properties):

    if dbType == 'blockchain':
        if properties['backend'] == 'leveldb':

            # import what's needed
            import neo.Storage.Implementation.LevelDB.LevelDBClassMethods as functions

            methods = [x for x in dir(functions) if not x.startswith('__')]

            # build attributes dict
            attributes = {methods[i]: getattr(
                functions, methods[i]) for i in range(0, len(methods))}

            # add __init__ method
            attributes['__init__'] = attributes.pop(functions._init_method)

            print(attributes)

            return type(
                        properties['backend'].title()+'DBImpl'+dbType.title(),
                        (AbstractDBInterface,),
                        attributes)

    if dbType == 'notification':
        raise Exception('Not yet implemented')

    if dbType == 'debug':
        raise Exception('Not yet implemented')


BlockchainDB = _dbFactory(BC_CONST, DATABASE_PROPS[BC_CONST])

# NotificationDB = _dbFactory(NOTIF_CONST, DATABASE_PROPS[NOTIF_CONST])

# DebugStorageDB = _dbFactory(DEBUG_CONST, DATABASE_PROPS[DEBUG_CONST])


_blockchain_db_instance = BlockchainDB(DATABASE_PROPS[BC_CONST]['path'])

# _notif_db_instance = NotificationDB(DATABASE_PROPS[NOTIF_CONST])

# _debug_db_instance = DebugStorageDB(DATABASE_PROPS[DEBUG_CONST])
