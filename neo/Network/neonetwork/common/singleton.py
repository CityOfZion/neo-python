"""
Courtesy of Guido: https://www.python.org/download/releases/2.2/descrintro/#__new__

To create a singleton class, you subclass from Singleton; each subclass will have a single instance, no matter how many times its constructor is called.
To further initialize the subclass instance, subclasses should override 'init' instead of __init__ - the __init__ method is called each time the constructor is called.
"""


class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass
