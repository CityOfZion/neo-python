from byteplay3 import SetLinenoType,Label,Opcode

from boa.code.token import PyToken,VMTokenizer
from boa.code.block import Block
from boa.code import pyop

import dis

import collections


class Method():

    bp = None

    parent = None

    tokens = None

    tokenizer = None

    local_stores = None

    start_line_no = None

    blocks = None

    method_address = None

    dynamic_iterator_count = 0

    local_methods = None

    __make_func_name=None

    @property
    def name(self):
        return self.bp.name


    @property
    def full_name(self):
        if self.__make_func_name is None:
            if len(self.module.module_path):
                return '%s.%s' % (self.module.module_path, self.name)
            return self.name
        return self.__make_func_name

    @property
    def args(self):
#        alist = list(self.bp.args)
#        if 'self' in alist:
#            alist.remove('self')
#        return alist
        return self.bp.args

    @property
    def code(self):
        return self.bp.code

    @property
    def vm_tokens(self):
        return self.tokenizer.vm_tokens


    @property
    def firstlineno(self):
        return self.bp.firstlineno

    @property
    def total_lines(self):
        count = 0
        for index,(op, arg) in enumerate(self.code):
            if type(op) is SetLinenoType:
                count +=1

        return count

    @property
    def module(self):

        from boa.code.module import Module

        if type(self.parent) is Module:
            return self.parent
        elif type(self.parent.parent) is Module:
            return self.parent.parent
        elif type(self.parent.parent.parent) is Module:
            return self.parent.parent.parent
        return None


    def __init__(self, code_object, parent, make_func_name=None):

        self.bp = code_object

        self.parent = parent

        self.__make_func_name = make_func_name

        self.read_initial_tokens()

        self.process_block_groups()

        self.tokenize()

        self.convert_jumps()

#        self.tokenizer.to_s()


    def print(self):
        print(self.code)


    def to_dis(self):

        out = self.bp.to_code()
        dis.dis(out)

    def read_initial_tokens(self):

        self.blocks = []

        self.local_methods = collections.OrderedDict()

        self.local_stores = collections.OrderedDict()

        current_line_no = None

        block_group = None

        self.tokenizer = VMTokenizer(self)

        current_label = None

        current_loop_token = None

        for i, (op, arg) in enumerate(self.code):

            #print("[%s] %s  ->  %s " % (i, op, arg))

            if type(op) is SetLinenoType:

                current_line_no = arg

                if self.start_line_no is None:
                    self.start_line_no = current_line_no

                if block_group is not None:

                    self.blocks.append( Block(block_group))

                block_group = []

            elif type(op) is Label:

                current_label = op

            else:


                if op == pyop.STORE_FAST and not arg in self.local_stores.keys():
                    length = len(self.local_stores)
                    self.local_stores[arg] = length

                token = PyToken(op, current_line_no,i, arg)

                if op == pyop.SETUP_LOOP:
                    current_loop_token = token

                if op == pyop.BREAK_LOOP and current_loop_token is not None:
                    token.args = current_loop_token.args
                    current_loop_token = None

                if current_label is not None:
                    token.jump_label = current_label
                    current_label = None

                block_group.append(token)

        if len(block_group):
            self.blocks.append( Block(block_group))


    def process_block_groups(self):

        iter_setup_block = None

        for index,block in enumerate(self.blocks):

            #if it is a return block
            #we need to insert a jmp at the start of the block
            #for the vm
            if block.is_return:

                #this jump needs to jump 3 bytes.  why? stay tuned to find out
                block_addr = b'\x03\x00'

                ret_token = PyToken(Opcode(pyop.BR_S),block.line,args=block_addr)
                ret_token.jump_label = block.oplist[0].jump_label
                block.oplist[0].jump_label = None
                block.oplist.insert(0, ret_token)
                block.mark_as_end()
#                length = len(self.local_stores)
#                self.local_stores[block.local_return_name] = length

            if block.has_make_function:

                block.preprocess_make_function(self)
                self.local_methods[block.local_func_varname] = block.local_func_name

            if block.is_list_comprehension:
                block.preprocess_list_comprehension(self)
                for localvar in block.list_comp_iterable_local_vars:
                    if localvar in self.local_stores.keys():
                        pass
                    else:
                        print("INSERTING LOCALVAR %s " % localvar)
                        length = len(self.local_stores)
                        self.local_stores[localvar] = length

            if block.has_slice:
                block.preprocess_slice()
                if block.slice_item_length is not None:
                    length = len(self.local_stores)
                    self.local_stores[block.slice_item_length] = length

            if block.has_unprocessed_array:
                block.preprocess_arrays()

            if block.has_unprocessed_array_sub:
                block.preprocess_array_subs()

            if block.has_unprocessed_method_calls:
                block.preprocess_method_calls(self)


            if iter_setup_block is not None:
                block.process_iter_body(iter_setup_block)
                iter_setup_block = None

            if block.is_iter and not block.is_list_comprehension:
                print("PROCESSING BLOCK ITER!!!!!!!")
                block.preprocess_iter()
                for localvar in block.iterable_local_vars:

                    if localvar in self.local_stores.keys():
                        pass
                    else:
                        length = len(self.local_stores)
                        self.local_stores[localvar] = length
                iter_setup_block = block
                self.dynamic_iterator_count +=1


        alltokens = []

        for block in self.blocks:
            if block.has_make_function:
                if block.is_list_comprehension:
                    alltokens = alltokens + block.oplist
            else:
                alltokens = alltokens + block.oplist
        self.tokens = alltokens

        for index,token in enumerate(self.tokens):
            token.addr = index

        print("LOCAL FUNC METHODS %s " % self.local_methods)

    def tokenize(self):
        self.tokenizer.update_method_begin_items()
        prevtoken = None
        for t in self.tokens:
            t.to_vm(self.tokenizer, prevtoken)
            prevtoken = t

    def convert_jumps(self):

        #convert normal jumps
        for key,vm_token in self.tokenizer.vm_tokens.items():

            if vm_token.pytoken and type(vm_token.pytoken.args) is Label:

                label = vm_token.pytoken.args

                for key2, vm_token_target in self.tokenizer.vm_tokens.items():

                    if vm_token_target.pytoken and vm_token_target.pytoken.jump_label is not None:

                        jump_to_label = vm_token_target.pytoken.jump_label

                        if jump_to_label == label:
#                            print("OP %s " % str(vm_token.pytoken.op_name))
#                            print("START/END: %s %s " % (vm_token_target.addr, vm_token.addr))

                            difference = vm_token_target.addr - vm_token.addr
#                            print("setting jump to %s " % difference)
                            vm_token.data = difference.to_bytes(2, 'little', signed=True)


    def write(self):


        out = self.tokenizer.to_b()
        return out

