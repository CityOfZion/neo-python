
from byteplay3 import Code, SetLinenoType,Label
from boa.code import pyop


from boa.code.line import Line
from boa.code.method import Method
from boa.code.items import Definition, Klass, Import,Action

from boa.blockchain.vm import VMOp

from collections import OrderedDict
import pdb

class Module():

    bp = None  # this is to store the byteplay reference

    path = None  # the path where this file is

    lines = None  # this contains the code objects split up into different line start indexes

    imports = None  # a list of import statements

    module_variables = None  # list of module variables

    classes = None  # a list of classes

    methods = None # a list to keep all methods in the module

    actions = None

    is_sys_module = None

    all_vm_tokens = None # dict for converting method tokens into linked method tokens for writing


    loaded_modules = None

    _module_name =None


    _names_to_load = None

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

        return om

    def add_method(self, method):
#        print("ADDING METHODDDDDD %s " % method.full_name)
        for m in self.methods:
            if m.name == method.name:

                if m.name != m.full_name:
                    if m.full_name == method.full_name:
                        return False
                else:
                    return False
#                return False

#        print("appending method %s %s " % (method.name, method.full_name))
        self.methods.append(method)

    def method_by_name(self, method_name):

        for m in self.methods:
            if m.full_name == method_name:
                return m
            elif m.name == method_name:
                return m
        return None

    def __init__(self, path, module_name='', is_sys_module=False, items_to_import=None):

        self.path = path

        self._module_name = module_name

        self.is_sys_module = is_sys_module

        if items_to_import == None:
            self._names_to_load = ['STAR']
        else:
            self._names_to_load = items_to_import

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
        self.actions = []
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
            elif lineset.is_action_registration:
                self.process_action(lineset)
            else:
                print('not sure what to do with line %s ' % lineset)
                pdb.set_trace()
                #print("code %s " % lineset.code_object)


    def process_import(self, import_item):

        self.imports.append(import_item)

        self.loaded_modules.append(import_item.imported_module)

        #go through all the methods in the imported module
        for method in import_item.imported_module.methods:
            self.add_method(method)

    def process_method(self, lineset):

        m = Method(lineset.code_object, self)

        if 'STAR' in self._names_to_load:
            self.add_method(m)
        else:

            for item in self._names_to_load:
                if item == m.name:
                    self.add_method(m)

    def process_action(self, lineset):
        action = Action(lineset)
        for act in self.actions:
            if act.method_name == action.method_name:
                return
        self.actions.append(action)

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

            for key, vmtoken in method.vm_tokens.items():

                self.all_vm_tokens[address] = vmtoken

                address += 1

                if vmtoken.data is not None:

                    address += len(vmtoken.data)

                vmtoken.addr = vmtoken.addr + method.method_address


        for key, vmtoken in self.all_vm_tokens.items():

            if vmtoken.src_method is not None:

                target_method = self.method_by_name( vmtoken.target_method )

                if target_method:

                    jump_len = target_method.method_address - vmtoken.addr
                    vmtoken.data = jump_len.to_bytes(2, 'little', signed=True)
                else:
                    raise Exception("Target method %s not found" % vmtoken.target_method)

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

                if pt.py_op == pyop.CALL_FUNCTION:
                    to_label = '%s %s ' % (pt.func_name, pt.func_params)

                lno = "{:<10}".format(pt.line_no if do_print_line_no or pstart else '')
                addr = "{:<4}".format(key)
                op = "{:<20}".format(str(pt.py_op))
                arg = "{:<50}".format(to_label if to_label is not None else pt.arg_s)
                data = "[data] {:<20}".format(ds)
                print("%s%s%s%s%s%s" % (lno, from_label, addr, op, arg, data))

            pstart = False
