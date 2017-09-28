
from byteplay3 import Code, SetLinenoType,Label


from boa.code.line import Line
from boa.code.method import Method
from boa.code.items import Definition, Klass, Import

from boa.blockchain.vm import VMOp

from collections import OrderedDict

class Module():

    bp = None  # this is to store the byteplay reference

    path = None  # the path where this file is

    lines = None  # this contains the code objects split up into different line start indexes

    imports = None  # a list of import statements

    module_variables = None  # list of module variables

    classes = None  # a list of classes

    methods = None # a list to keep all methods in the module

    is_sys_module = None

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
        self.methods.reverse()
        if self.main:
            om = [self.main]

        for m in self.methods:
            if m == self.main:
                continue
            om.append(m)

        for k in om:
            print("MEthed:  ->  %s " % (k.name))

        return om

    def add_method(self, method):
        for m in self.methods:
#            print("comparing method... %s %s " % (m.name, method.name))
            if m.name == method.name:
#                print("method %s already added " % m.name)
                return False

#        from boa.boa import Compiler
#        if self == Compiler.instance().default:
        print("[%s]     Adding method %s %s " % (self.module_path,method.name, method))

        self.methods.append(method)

    def method_by_name(self, method_name):
        for m in self.methods:
            if m.name == method_name:
                return m
        return None

    def __init__(self, path, module_name='', is_sys_module=False):

        self.path = path

        self._module_name = module_name

        self.is_sys_module = is_sys_module

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

                if not self.is_sys_module:
                    imp = Import(lineset.items)
                    self.process_import(imp)
                else:
                    print("will not import items from sys module")

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
            self.add_method(method)

    def process_method(self, lineset):

        m = Method(lineset.code_object, self)
#        print("Adding method %s %s " % (m.name, m))
        self.add_method(m)
#        self.methods.append(m)

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

            if vm_token.data is not None and vm_token.vm_op != VMOp.NOP:
                b_array = b_array + vm_token.data

        return b_array


    def link_methods(self):

        self.all_vm_tokens = OrderedDict()

        address = 0

        for method in self.orderered_methods:

            method.method_address = address
            print("METHOD, ADDRESS %s %s" % (method.name, address) )
            for key, vmtoken in method.vm_tokens.items():

                self.all_vm_tokens[address] = vmtoken

                address += 1

                if vmtoken.data is not None:

                    address += len(vmtoken.data)

                vmtoken.addr = vmtoken.addr + method.method_address


        for key, vmtoken in self.all_vm_tokens.items():

            if vmtoken.src_method is not None:


                target_method = self.method_by_name( vmtoken.target_method )
                print("TARGET METHOD IS %s %s " % (target_method, vmtoken.src_method))
                jump_len = target_method.method_address - vmtoken.addr
                print("method address... token address %s %s " % (target_method.method_address, vmtoken.addr))
                print("JUMP LEN %s " % jump_len)
                jbytes = jump_len.to_bytes(2, 'little',signed=True)
                print("jbytes %s " % jbytes)
                vmtoken.data = jump_len.to_bytes(2, 'little', signed=True)


    def to_s(self):

        lineno = 0
        pstart = True
        for i, (key, value) in enumerate(self.all_vm_tokens.items()):

            if value.pytoken:
                pt = value.pytoken

                do_print_line_no = False
                to_label = None
                from_label = '    '
                if pt.line_no != lineno:
                    print("\n")
                    lineno = pt.line_no
                    do_print_line_no = True

                if pt.args and type(pt.args) is Label:
                    addr = value.addr
                    if value.data is not None:
                        plus_addr = int.from_bytes(value.data, 'little', signed=True)
                        target_addr = addr + plus_addr
                        to_label = 'to %s    [ %s ]' % (target_addr, pt.args)
                    else:
                        to_label = 'from << %s ' % pt.args
                        #                    to_label = 'to %s ' % pt.args
                elif pt.jump_label:
                    from_label = ' >> '
                    to_label = 'from [%s]' % pt.jump_label

                ds = ''
                if value.data is not None:
                    try:
                        ds = int.from_bytes(value.data, 'little', signed=True)
                    except Exception as e:
                        pass
                    if type(ds) is not int and len(ds) < 1:
                        try:
                            ds = value.data.decode('utf-8')
                        except Exception as e:
                            pass

                lno = "{:<10}".format(pt.line_no if do_print_line_no or pstart else '')
                addr = "{:<4}".format(key)
                op = "{:<20}".format(str(pt.py_op))
                arg = "{:<50}".format(to_label if to_label is not None else pt.arg_s)
                data = "[data] {:<20}".format(ds)
                print("%s%s%s%s%s%s" % (lno, from_label, addr, op, arg, data))

            pstart = False
