from byteplay3 import SetLinenoType,Opcode,Label

from boa.code.token import PyToken,VMToken,VMTokenizer
from boa.code import pyop

import dis




class Block():

    oplist = None # list

    _label = None # list

    def __init__(self, operation_list):
        self.oplist = operation_list

    def set_label(self, label):
        self._label = label
        self.oplist[0].jump_label = label

    @property
    def line(self):
        if len(self.oplist):
            token = self.oplist[0]
            return token.line_no
        return None

    @property
    def is_return(self):
        if len(self.oplist):
            token = self.oplist[-1]
            if token.py_op == pyop.RETURN_VALUE:
                return True



        return False

    def mark_as_end(self):

        tstart = self.oplist[:-1]
        tend = self.oplist[-1:]

        newitems = [PyToken(pyop.NOP,self.line), PyToken(pyop.FROMALTSTACK, self.line), PyToken(pyop.DROP, self.line)]

        self.oplist = tstart + newitems + tend


    def __str__(self):
        if self._label:
            return '[Block] %s          [label] %s' % (self.oplist, self._label)
        return '[Block]: %s' % self.oplist


class Method():

    bp = None

    parent = None

    tokens = None

    tokenizer = None


    local_stores = None

    start_line_no = None

    blocks = None

    @property
    def name(self):
        return self.bp.name

    @property
    def args(self):
        return self.bp.args

    @property
    def code(self):
        return self.bp.code

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


    def __init__(self, code_object, parent):


        self.bp = code_object

        self.parent = parent

        if not self in self.module.methods:
            self.module.methods.append(self)

        self.read_initial_tokens()

        self.process_block_groups()

        self.tokenize()

        self.convert_jumps()

    def print(self):
        print(self.code)


    def to_dis(self):

        out = self.bp.to_code()
        dis.dis(out)

    def read_initial_tokens(self):

        self.blocks = []

        self.local_stores = {}

        current_line_no = None

        block_group = None

        self.tokenizer = VMTokenizer(self)

        labels = {}


        for i, (op, arg) in enumerate(self.code):

            if type(op) is SetLinenoType:

                current_line_no = arg

                if self.start_line_no is None:
                    self.start_line_no = current_line_no

                if block_group is not None:

                    self.blocks.append( Block(block_group))

                block_group = []

            elif type(op) is Label:
                labels[1 + len(self.blocks)] = op
            else:
                if op == pyop.STORE_FAST and not arg in self.local_stores.keys():
                    length = len(self.local_stores)
                    self.local_stores[arg] = length

                token = PyToken(op, current_line_no,i, arg)

                block_group.append(token)

        if len(block_group):
            self.blocks.append( Block(block_group))


        for key,label in labels.items():
            kint = int(key)
            self.blocks[kint].set_label(label)

#        [print("block: %s " % str(block)) for block in self.blocks]

    def process_block_groups(self):

        for index,block in enumerate(self.blocks):

            #if it is a return block
            #we need to insert a jmp at the start of the block
            #for the vm
            if block.is_return:

                #this jump needs to jump 3 bytes.  why? stay tuned to find out
                block_addr = b'\x03\x00'

                ret_token = PyToken(pyop.BR_S,block.line,args=block_addr)
                ret_token.jump_label = block.oplist[0].jump_label
                block.oplist[0].jump_label = None
                block.oplist.insert(0, ret_token)
                block.mark_as_end()


        alltokens = []
        for block in self.blocks:
            alltokens = alltokens + block.oplist

        self.tokens = alltokens

        for index,token in enumerate(self.tokens):
            token.addr = index


    def tokenize(self):

        for t in self.tokens:
            t.to_vm(self.tokenizer)


    def convert_jumps(self):
        for key,vm_token in self.tokenizer.vm_tokens.items():

            if vm_token.pytoken and type(vm_token.pytoken.args) is Label:

                label = vm_token.pytoken.args

                for key2, vm_token_target in self.tokenizer.vm_tokens.items():

                    if vm_token_target.pytoken and vm_token_target.pytoken.jump_label is not None:

                        jump_to_label = vm_token_target.pytoken.jump_label

                        if jump_to_label == label:

                            difference = vm_token_target.addr - vm_token.addr
                            vm_token.data = difference.to_bytes(2, 'little')


    def write(self):

        self.tokenizer.to_s()

        out = self.tokenizer.to_b()
        return out
