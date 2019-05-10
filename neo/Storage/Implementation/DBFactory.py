from neo.Storage.Implementation.AbstractDBImplementation import (
    AbstractDBImplementation
)
from neo.Settings import settings
from neo.logging import log_manager


"""Database factory module

Note:
    Module is used to access the different database implementations.
    Import the module and use the getters to access the different databases.
    Configuration is done in neo.Settings.DATABASE_PROPS dict.
    Each getter returns an instance of the database.

Constants:
    BC_CONST (str): defines the key within the settings.database_properties()
                    to retrieve the blockchain db properties.

    NOTIF_CONST (str): defines the key within the settings.database_properties()
                       to retrieve the notification db properties.

    DEBUG_CONST (str): defines the key within the settings.database_properties()
                       to retrieve the debug storage properties.

    DATABASE_PROPS (dict): The properties defined within the settings module.

"""

logger = log_manager.getLogger()

BC_CONST = 'blockchain'
NOTIF_CONST = 'notification'
DEBUG_CONST = 'debug'

DATABASE_PROPS = settings.database_properties()


def getBlockchainDB(path=None):
    """
    Returns a database instance used with the blockchain class.

    Args:
        path (str, optional): the full path to the blockchain database directory.

    Returns:
        _blockchain_db_instance (object): A new blockchain database instance.
    """

    if not path:
        path = DATABASE_PROPS[BC_CONST]['path']

    BlockchainDB = _dbFactory(BC_CONST, DATABASE_PROPS[BC_CONST])
    _blockchain_db_instance = BlockchainDB(path)
    return _blockchain_db_instance


def getNotificationDB(path=None):
    """
    Returns a database instance used with the notification class.

    Args:
        path (str, optional): the full path to the notification database directory.

    Returns:
        _notif_db_instance (object): A new notification database instance.
    """

    if not path:
        path = DATABASE_PROPS[NOTIF_CONST]['path']

    NotificationDB = _dbFactory(NOTIF_CONST, DATABASE_PROPS[NOTIF_CONST])
    _notif_db_instance = NotificationDB(path)
    return _notif_db_instance


def getDebugStorageDB():
    """
    Returns a database instance used with the debug storage class.

    Returns:
        _debug_db_instance (object): A new debug storage instance.
    """

    DebugStorageDB = _dbFactory(DEBUG_CONST, DATABASE_PROPS[DEBUG_CONST])
    _debug_db_instance = DebugStorageDB(DATABASE_PROPS[DEBUG_CONST]['path'])
    return _debug_db_instance


def _dbFactory(dbType, properties):
    """ Method to generate a database class.

    Args:
        dbType (str): Type of the database (Blockchain, Notification, Debug).
        properties (dict): The properties defined within the settings module.

    Returns:
        New database class to instantiate a new database.


    """

    if properties['backend'] == 'leveldb':

        """
        Module implements the methods used by the dynamically generated class.
        """
        import neo.Storage.Implementation.LevelDB.LevelDBClassMethods as functions

        methods = [x for x in dir(functions) if not x.startswith('__')]

        # build the dict containing all the attributes (methods + members)
        attributes = {methods[i]: getattr(
            functions, methods[i]) for i in range(0, len(methods))}

        # add __init__ method
        attributes['__init__'] = attributes.pop(functions._init_method)

        return type(
            properties['backend'].title() + 'DBImpl' + dbType.title(),
            (AbstractDBImplementation,),
            attributes)
