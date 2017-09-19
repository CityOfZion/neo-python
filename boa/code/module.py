
from byteplay3 import Code, SetLinenoType


from boa.code.line import Line
from boa.code.items import Definition, Klass, Import


class Module():

    bp = None  # this is to store the byteplay reference

    path = None  # the path where this file is

    lines = None  # this contains the code objects split up into different line start indexes

    imports = None  # a list of import statements

    module_variables = None  # list of module variables

    classes = None  # a list of classes

    methods = None # a list to keep all methods in the module

    @property
    def main(self):
        for m in self.methods:
            if m.name=='Main':
                return m
        if len(self.methods):
            return self.methods[0]
        return None

    def __init__(self, path):

        self.path = path

        source = open(path, 'rb')

        suite = compile(source.read(), path, 'exec')

        self.bp = Code.from_code(suite)

        source.close()

        self.build()

    def build(self):

        self.lines = []
        self.imports = []
        self.module_variables = []
        self.methods = []
        self.classes = []

        self.split_lines()

        for lineset in self.lines:

            if lineset.is_import:
                self.imports.append(Import(lineset.items))
            elif lineset.is_definition:
                self.module_variables.append(Definition(lineset.items))
            elif lineset.is_class:
                self.classes.append(Klass(lineset.items, self))
            else:
                print('not sure what to do with line %s ' % lineset)

        self.validate_imports()

        self.build_classes()

    def split_lines(self):

        lineitem = None

        for i, (op, arg) in enumerate(self.bp.code):

            if isinstance(op, SetLinenoType):
                if lineitem is not None:
                    self.lines.append(Line(lineitem))

                lineitem = []

            lineitem.append((op, arg))

        if len(lineitem):
            self.lines.append(Line(lineitem))

    def validate_imports(self):
        #print('will validate imports... %s ' % self.imports)
        pass

    def build_classes(self):
        #print('build classes %s ' % self.classes)
        pass
