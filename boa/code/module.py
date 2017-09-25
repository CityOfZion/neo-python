
from byteplay3 import Code, SetLinenoType


from boa.code.line import Line
from boa.code.method import Method
from boa.code.items import Definition, Klass, Import

from neo.VM import OpCode


from collections import OrderedDict

class Module():

    bp = None  # this is to store the byteplay reference

    path = None  # the path where this file is

    lines = None  # this contains the code objects split up into different line start indexes

    imports = None  # a list of import statements

    module_variables = None  # list of module variables

    classes = None  # a list of classes

    methods = None # a list to keep all methods in the module


    all_vm_tokens = None # dict for converting method tokens into linked method tokens for writing


    loaded_modules = None

    _module_name =None


    @property
    def module_path(self):
        return self._module_name



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

    def __init__(self, path, module_name=''):

        self.path = path

        self._module_name = module_name

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
        self.loaded_modules = []

        self.split_lines()

        for lineset in self.lines:

            if lineset.is_import:
                imp = Import(lineset.items)
                self.process_import(imp)
            elif lineset.is_definition:
                self.module_variables.append(Definition(lineset.items))
            elif lineset.is_class:
                self.classes.append(Klass(lineset.items, self))
            elif lineset.is_method:
                self.process_method(lineset)
            else:
                print('not sure what to do with line %s ' % lineset)



    def process_import(self, import_item):
        self.imports.append(import_item)

        self.loaded_modules.append(import_item.imported_module)

        #go through all the methods in the imported module
        for method in import_item.imported_module.methods:

            #go through the methods in this module
            do_add = True
            for method2 in self.methods:

                #check to see if a method with that definition is loaded
                if method.name == method2.name:
                    do_add = False
                    print("already imported method named %s %s %s" % (import_item.imported_module, method,method2 ))


            #if it hasn't been defined, add it to this modules' methods

            self.methods.append(method)

    def process_method(self, lineset):

        m = Method(lineset.code_object, self)
        self.methods.append(m)

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




    def write(self):


        self.link_methods()

        return self.write_methods()


    def write_methods(self):

        b_array = bytearray()
        for key, vm_token in self.all_vm_tokens.items():

            b_array.append(vm_token.out_op)

            if vm_token.data is not None and vm_token.vm_op != OpCode.NOP:
                b_array = b_array + vm_token.data

        return b_array


    def link_methods(self):

        self.all_vm_tokens = OrderedDict()

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

                print("vm token target method %s " % vmtoken.target_method)

                target_method = self.method_by_name( vmtoken.target_method )

                jump_len = target_method.method_address - vmtoken.addr

                vmtoken.data = jump_len.to_bytes(2, 'little', signed=True)

