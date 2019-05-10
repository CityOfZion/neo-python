from neo.Storage.Implementation.AbstractDBImplementation import AbstractDBImplementation


def internalDBFactory(classPrefix):
    """ Internal database factory method used for prefixed dbs and snapshots.

    The returned class is very similar the the class returned in
    neo.Storage.Implementation.DBFactory._dbFactory but has a different
    __init__ method.

    Args:
        classPrefix (str): Prefix to name the class appropiately.

    Returns:
        classPrefix + DBImpl (object): dynamically generated class used for
                                       PrefixedDBs and SnapshotDBs.

    """

    # import what's needed
    import neo.Storage.Implementation.LevelDB.LevelDBClassMethods as functions

    methods = [x for x in dir(functions) if not x.startswith('__')]

    # build attributes dict
    attributes = {methods[i]: getattr(
        functions, methods[i]) for i in range(0, len(methods))}

    # add __init__ method
    attributes['__init__'] = attributes.pop(functions._prefix_init_method)

    return type(
        classPrefix.title() + 'DBImpl',
        (AbstractDBImplementation,),
        attributes)
