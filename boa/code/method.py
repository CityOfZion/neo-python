from byteplay3 import SetLinenoType,Opcode

from boa.code.token import PyToken,VMToken,VMTokenizer
from boa.code import pyop

import dis




class Block():

    oplist = None # list

    def __init__(self, operation_list):
        self.oplist = operation_list

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


        for i, (op, arg) in enumerate(self.code):

            if type(op) is SetLinenoType:

                current_line_no = arg

                if self.start_line_no is None:
                    self.start_line_no = current_line_no

                if block_group is not None:

                    self.blocks.append( Block(block_group))
                block_group = []

            else:

                if op == pyop.STORE_FAST and not arg in self.local_stores.keys():
                    length = len(self.local_stores)
                    self.local_stores[arg] = length

                token = PyToken(op, current_line_no,i, arg)

                block_group.append(token)


        if len(block_group):
            self.blocks.append( Block(block_group))


#    def insert_arguments(self):

    def process_block_groups(self):

        for index,block in enumerate(self.blocks):

            #if it is a return block
            #we need to insert a jmp at the start of the block
            #for the vm
            if block.is_return:

                #this jump needs to jump 3 bytes.  why? stay tuned to find out
                block_addr = b'\x03\x00'
                ret_token = PyToken(Opcode(pyop.JUMP_FORWARD),block.line,args=block_addr)
                block.oplist.insert(0, ret_token)


        #now we have to get the last block ( which should be a return block )
        #and insert the 'end code' for the vm

        last_block = self.blocks[-1]
        last_block.mark_as_end()

        alltokens = []
        for block in self.blocks:
            alltokens = alltokens + block.oplist

        self.tokens = alltokens

        for index,token in enumerate(self.tokens):
            token.addr = index


    def tokenize(self):

        for t in self.tokens:
            t.to_vm(self.tokenizer)


    def write(self):

        self.tokenizer.to_s()

        out = self.tokenizer.to_b()
        return out
