from byteplay3 import Code
from boa.code.method import Method


class Item():
    items = None

    def __init__(self, item_list):
        self.items = item_list

    def is_valid(self):
        return True


class Definition(Item):
    pass


class Import(Item):

    def is_valid(self):
        # here is where we will check imports
        return True


class Klass(Item):

    name = None

    parent = None

    methods = None

    bp = None

    def __init__(self, item_list):
        super(Klass, self).__init__(item_list)
        self.methods = []
        self.build()

    def build(self):

        for i, (op, arg) in enumerate(self.items):

            # if the item is a byteplay3 code object, it is a method
            if type(arg) is Code:
                self.bp = arg

            # load name is called  to gather the class parent
            if str(op) == 'LOAD_NAME':
                self.parent = arg

            # this occurs to store the name of the class
            if str(op) == 'STORE_NAME':
                self.name = arg

        print('Created class %s inherits from %s ' % (self.name, self.parent))

        # go through code object of the class and extract the method code
        # objects
        for i, (op, arg) in enumerate(self.bp.code):

            if type(arg) is Code:
                self.methods.append(Method(arg))

    def is_valid(self):
        # here is where we check if the class extends something reasonable
        return True
