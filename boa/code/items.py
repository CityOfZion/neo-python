from byteplay3 import Code
from boa.code.method import Method
from boa.code import pyop
import importlib
import pdb

class Item():
    items = None

    def __init__(self, item_list):
        self.items = item_list

    def is_valid(self):
        return True


class Definition(Item):
    pass


class Import(Item):

    module_path = None
    module_name = None


    imported_module = None

    def __init__(self, item_list):
        super(Import, self).__init__(item_list)

        for i, (op, arg) in enumerate(self.items):
            if op == pyop.IMPORT_NAME:
                self.module_path = arg

            elif op == pyop.STORE_NAME:
                self.module_name = arg

        self.build()

    def build(self):
        # here is where we will check imports

        from boa.code.module import Module

        module = importlib.import_module(self.module_path, self.module_path)

        filename = module.__file__

        self.imported_module = Module(filename, module_name=self.module_path)


    def is_valid(self):

        return True

    def __str__(self):
        return "%s.%s" % (self.module_path, self.module_name)

class Klass(Item):

    name = None

    parent_name = None

    parent = None

    methods = None

    bp = None

    module = None

    def __init__(self, item_list, module):
        super(Klass, self).__init__(item_list)
        self.module = self.parent = module
        self.methods = []
        self.build()

    def build(self):

        for i, (op, arg) in enumerate(self.items):

            # if the item is a byteplay3 code object, it is a method
            if type(arg) is Code:
                self.bp = arg

            # load name is called  to gather the class parent
            if op == pyop.LOAD_NAME:
                self.parent_name = arg

            # this occurs to store the name of the class
            if op == pyop.STORE_NAME:
                self.name = arg

#        print('Created class %s inherits from %s ' % (self.name, self.parent))

        # go through code object of the class and extract the method code
        # objects
        for i, (op, arg) in enumerate(self.bp.code):

            if type(arg) is Code:
                self.methods.append(Method(arg, self))

    def is_valid(self):
        # here is where we check if the class extends something reasonable
        return True
