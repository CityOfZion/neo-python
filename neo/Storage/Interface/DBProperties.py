class DBProperties:
    """
    Container for holding DB properties
    Used to pass the configuration options to the DB iterator initializer.
    neo.Storage.Implementation.[BACKEND].[BACKEND]Impl.openIter

    Args:
        prefix (str, optional): Prefix to search for.
        include_value (bool, optional): whether to include keys in the returned data
        include_key (bool, optional): whether to include values in the returned data
    """

    def __init__(self, prefix=None, include_value=True, include_key=True):

        if not include_value and not include_key:
            raise Exception('Either key or value have to be true')

        self.prefix = prefix
        self.include_value = include_value
        self.include_key = include_key
