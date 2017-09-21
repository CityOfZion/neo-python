
from byteplay3 import Code, SetLinenoType


from boa.code.line import Line
from boa.code.method import Method
from boa.code.items import Definition, Klass, Import

import sys

class Module():

    bp = None  # this is to store the byteplay reference

    path = None  # the path where this file is

    lines = None  # this contains the code objects split up into different line start indexes

    imports = None  # a list of import statements

    module_variables = None  # list of module variables

    classes = None  # a list of classes

    methods = None # a list to keep all methods in the module


    all_vm_tokens = None # dict for converting method tokens into linked method tokens for writing


    @property
    def main_path(self):
        return sys.modules['__main__']

    @property
    def module_path(self):
        return sys.modules['__main__'].__file__

    @property
    def main(self):
        for m in self.methods:
            if m.name=='Main':
                return m
        if len(self.methods):
            return self.methods[0]
        return None

    @property
    def orderered_methods(self):
        om = []

        if self.main:
            om = [self.main]

        for m in self.methods:
            if m == self.main:
                continue
            om.append(m)

        return om

    def method_by_name(self, method_name):
        for m in self.methods:
            if m.name == method_name:
                return m
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
            elif lineset.is_method:
                self.methods.append(Method(lineset.code_object, self))
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



    def write(self):


        self.link_methods()

        return self.write_methods()


    def write_methods(self):

        b_array = bytearray()
        for key, vm_token in self.all_vm_tokens.items():

            b_array.append(vm_token.out_op)

            if vm_token.data is not None:
                b_array = b_array + vm_token.data

        return b_array


    def link_methods(self):

        self.all_vm_tokens = {}

        address = 0

        for method in self.orderered_methods:

            method.method_address = address

            for key, vmtoken in method.vm_tokens.items():

                self.all_vm_tokens[address] = vmtoken

                address += 1

                if vmtoken.data is not None:

                    address += len(vmtoken.data)

                vmtoken.addr = vmtoken.addr + method.method_address


        for key, vmtoken in self.all_vm_tokens.items():

            if vmtoken.src_method is not None:

                target_method = self.method_by_name( vmtoken.target_method )

                jump_len = target_method.method_address - vmtoken.addr

                vmtoken.data = jump_len.to_bytes(2, 'little', signed=True)

