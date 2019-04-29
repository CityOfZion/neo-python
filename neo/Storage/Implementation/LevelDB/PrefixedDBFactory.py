from neo.Storage.Implementation.AbstractDBImplementation import AbstractDBImplementation


def internalDBFactory(classPrefix):

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
