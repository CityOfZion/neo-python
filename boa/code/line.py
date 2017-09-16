
class Line():

    items = None

    def __init__(self, item_list):
        self.items = item_list

    @property
    def is_import(self):
        for i, (op, arg) in enumerate(self.items):
            if str(op) in ['IMPORT_NAME', 'IMPORT_FROM']:
                return True
        return False

    @property
    def is_definition(self):
        return len(self.items) == 3 and str(self.items[1][0]) == 'LOAD_CONST' and str(self.items[2][0]) == 'STORE_NAME'
#        return False

    @property
    def is_class(self):
        for i, (op, arg) in enumerate(self.items):
            if str(op) == 'LOAD_BUILD_CLASS':
                return True
        return False
