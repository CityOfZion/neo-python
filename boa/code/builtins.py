

class list(list):

    def __init__(self, length=0):
#        super(list, self).__init__()
        pass

    """
    list() -> new empty list
    list(length=x) -> new list initialized with length of x
    """


#    The following items are not currently supported by the compiler or VM
#
#    def append(self, p_object):  # real signature unknown; restored from __doc__
#        """ L.append(object) -> None -- append object to end """
#        pass
#
#    def clear(self):  # real signature unknown; restored from __doc__
#        """ L.clear() -> None -- remove all items from L """
#        pass
#
#    def copy(self):  # real signature unknown; restored from __doc__
#        """ L.copy() -> list -- a shallow copy of L """
#        return []
#
#    def count(self, value):  # real signature unknown; restored from __doc__
#        """ L.count(value) -> integer -- return number of occurrences of value """
#        return 0
#
#    def extend(self, iterable):  # real signature unknown; restored from __doc__
#        """ L.extend(iterable) -> None -- extend list by appending elements from the iterable """
#        pass
#
#    def index(self, value, start=None, stop=None):  # real signature unknown; restored from __doc__
#        """
#        L.index(value, [start, [stop]]) -> integer -- return first index of value.
#        Raises ValueError if the value is not present.
#        """
#        return 0
#
#    def insert(self, index, p_object):  # real signature unknown; restored from __doc__
#        """ L.insert(index, object) -- insert object before index """
#        pass
#
#    def pop(self, index=None):  # real signature unknown; restored from __doc__
#        """
#        L.pop([index]) -> item -- remove and return item at index (default last).
#        Raises IndexError if list is empty or index is out of range.
#        """
#        pass
#
#    def remove(self, value):  # real signature unknown; restored from __doc__
#        """
#        L.remove(value) -> None -- remove first occurrence of value.
#        Raises ValueError if the value is not present.
#        """
#        pass
#
#    def reverse(self):  # real signature unknown; restored from __doc__
#        """ L.reverse() -- reverse *IN PLACE* """
#        pass
#
#    def sort(self, key=None, reverse=False):  # real signature unknown; restored from __doc__
#        """ L.sort(key=None, reverse=False) -> None -- stable sort *IN PLACE* """
#        pass


    def __contains__(self, *args, **kwargs):  # real signature unknown
        """ Return key in self. """
        pass


    def __eq__(self, *args, **kwargs):  # real signature unknown
        """ Return self==value. """
        pass


    def __getitem__(self, y):  # real signature unknown; restored from __doc__
        """ x.__getitem__(y) <==> x[y] """
        pass

    def __setitem__(self, *args, **kwargs):  # real signature unknown
        """ Set self[key] to value. """
        pass



def concat(str1, str2):
    """
     range(str1, str2) -> str object

     Return a string that is the concatenation of the two arguments ( str1 + str2 )
     """
    pass


# This is not necessary.  you can use mystring[start:end]
#def substr(source,start_index, count):
#    """
#    substr(source, start_index, count) -> list object
#
#    Return a subset of a string `source`, starting at `start_index` and
#    of length `count`
#    """
#    pass


def take(source, count):
    """
    take(source, count) -> list object

    Return a subset of a string or list `source`, starting
    at index 0 and of length `count`
    """
    pass


def range(start, stop):
    """
    range(start, stop) -> list object

    Return an list that is a a sequence of integers from start (inclusive)
    to stop (exclusive).  range(i, j) produces i, i+1, i+2, ..., j-1.
    """

    length = stop - start

    out = list(length=length)

    index = 0

    orig_start = start

    while start < stop:
        val = index + orig_start
        out[index] = val
        index = index + 1
        start = orig_start + index

    return out


def sha1(data):
    pass

def sha256(data):
    pass

def hash160(data):
    pass

def hash256(data):
    pass

def verify_signature(signature, pubkey):
    pass

def verify_signatures(signatures, pubkeys):
    pass
