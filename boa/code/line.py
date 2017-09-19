from byteplay3 import *

from boa.code import pyop

class Line():

    items = None

    def __init__(self, item_list):
        self.items = item_list

    @property
    def is_import(self):
        for i, (op, arg) in enumerate(self.items):
            if op in [pyop.IMPORT_NAME, pyop.IMPORT_FROM, pyop.IMPORT_STAR]:
                return True
        return False

    @property
    def is_definition(self):
        return len(self.items) == 3 and self.items[1][0] == pyop.LOAD_CONST and self.items[2][0] == pyop.STORE_NAME
#        return False

    @property
    def is_class(self):
        for i, (op, arg) in enumerate(self.items):
            if op == pyop.LOAD_BUILD_CLASS:
                return True
        return False
