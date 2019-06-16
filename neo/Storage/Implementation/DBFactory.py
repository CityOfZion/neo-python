from neo.Settings import settings
from neo.Utils.plugin import load_class_from_path

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

BC_CONST = 'Blockchain'
NOTIF_CONST = 'Notification'
DEBUG_CONST = 'DebugStorage'


def getBlockchainDB(path=None):
    """
    Returns a database instance used with the blockchain class.

    Args:
        path (str, optional): the full path to the blockchain database directory.

    Returns:
        _blockchain_db_instance (object): A new blockchain database instance.
    """

    DATABASE_PROPS = settings.database_properties()
    if not path:
        path = DATABASE_PROPS[BC_CONST]['DataDirectoryPath']

    BlockchainDB = load_class_from_path(DATABASE_PROPS[BC_CONST]['backend'])
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

    DATABASE_PROPS = settings.database_properties()
    if not path:
        path = DATABASE_PROPS[NOTIF_CONST]['NotificationDataPath']

    NotificationDB = load_class_from_path(DATABASE_PROPS[NOTIF_CONST]['backend'])
    _notif_db_instance = NotificationDB(path)
    return _notif_db_instance


def getDebugStorageDB():
    """
    Returns a database instance used with the debug storage class.

    Returns:
        _debug_db_instance (object): A new debug storage instance.
    """

    DATABASE_PROPS = settings.database_properties()
    DebugStorageDB = load_class_from_path(DATABASE_PROPS[DEBUG_CONST]['backend'])
    _debug_db_instance = DebugStorageDB(DATABASE_PROPS[DEBUG_CONST]['DebugStoragePath'])
    return _debug_db_instance
