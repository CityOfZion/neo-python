from boa.code import pyop

from byteplay3 import Label,isopcode,haslocal

from opcode import opname

from neo.VM import OpCode

from neo.BigInteger import BigInteger



class PyToken():

    py_op = None

    args = None

    line_no = None

    addr = None

    tokenizer = None

    jump_label = None

    @property
    def op_name(self):
        if type(self.py_op) is int:
            return opname[self.py_op]
        elif type(self.py_op) is Label:
            return 'Label %s ' % self.py_op
        return self.py_op

    @property
    def is_op(self):
        return isopcode(self.py_op)

    @property
    def is_local(self):
        return haslocal(self.py_op)

    @property
    def arg_s(self):
        if self.args:
            return str(self.args)
        return ''

    def __init__(self, op, lineno, index=None,args=None):

        self.py_op = op

        self.args = args

        self.line_no = lineno

        self.addr = index


    def __str__(self):
        arg = ''

        if self.args:
            if type(self.args) is Label:
                arg = str(self.args)
            else:
                arg = self.args
            return '%s      %s   %s  --> %s ' % (self.line_no, self.addr, self.op_name, arg)
        return '%s      %s   %s' % (self.line_no, self.addr, self.op_name)


    def to_vm(self, tokenizer):

        self.tokenizer = tokenizer
        token = None

        if self.is_op:

            op = self.py_op

            if op == pyop.NOP:
                token = tokenizer.convert1(OpCode.NOP, self)

            elif op == pyop.RETURN_VALUE:
                token = tokenizer.convert1(OpCode.RET, self)

            elif op == pyop.POP_BLOCK:
                token = tokenizer.convert1(OpCode.DROP)

            #elif op == pyop.LOAD_NULL // this doesn't exist
            #   self.vm_op = byte(0)


            #control flow
            elif op == pyop.BR_S:
                token = tokenizer.convert1(OpCode.JMP, self, data=self.args)

            elif op == pyop.JUMP_FORWARD:
                token = tokenizer.convert1(OpCode.JMP,self, data=bytearray(2))

            elif op == pyop.JUMP_ABSOLUTE:
                token = tokenizer.convert1(OpCode.JMP,self, data=bytearray(2))

            elif op == pyop.POP_JUMP_IF_FALSE:
                token = tokenizer.convert1(OpCode.JMPIFNOT, self, data=bytearray(2))


            elif op == pyop.FROMALTSTACK:
                token = tokenizer.convert1(OpCode.FROMALTSTACK, self)
            elif op == pyop.DROP:
                token = tokenizer.convert1(OpCode.DROP, self)

            #loading constants ( ie 1, 2 etc)
            elif op == pyop.LOAD_CONST:
                if type(self.args) is int:
                    token = tokenizer.convert_push_integer(self.args, self)
                elif type(self.args) is str:

                    str_bytes = self.args.encode('utf-8')
                    self.args = str_bytes
                    print("convert argument %s " % self.args)

                    token = tokenizer.convert_push_data(self.args, self)

            #storing / loading local variables
            elif op == pyop.STORE_FAST:
                token = tokenizer.convert_store_local(self)

            elif op == pyop.LOAD_FAST:
                token = tokenizer.convert_load_local(self)


            #math
            elif op == pyop.BINARY_ADD:
                token = tokenizer.convert1(OpCode.ADD, self)

            elif op == pyop.BINARY_SUBTRACT:
                token = tokenizer.convert1(OpCode.SUB, self)

            elif op == pyop.BINARY_MULTIPLY:
                token = tokenizer.convert1(OpCode.MUL, self)

            elif op in [pyop.BINARY_FLOOR_DIVIDE, pyop.BINARY_TRUE_DIVIDE]:
                token = tokenizer.convert1(OpCode.DIV, self)

            elif op == pyop.BINARY_MODULO:
                token = tokenizer.convert1(OpCode.MOD, self)


            #compare

            elif op == pyop.COMPARE_OP:

                if self.args == '>':
                    token = tokenizer.convert1(OpCode.GT, self)
                elif self.args == '>=':
                    token = tokenizer.convert1(OpCode.GTE, self)
                elif self.args == '<':
                    token = tokenizer.convert1(OpCode.LT, self)
                elif self.args == '<=':
                    token = tokenizer.convert1(OpCode.LTE, self)
                elif self.args == '==':
                    token = tokenizer.convert1(OpCode.EQUAL, self)

#                tokn = tokenizer.convert1(Op)

#        print("created vm token %s " % token)
#
#        if token is None:
#            print("did not get token for %s %s" % (self, self.op_name))

class VMToken():

    addr = None

    pytoken = None

    data = None

    vm_op = None


    @property
    def out_op(self):
        if type(self.vm_op) is int:
            return self.vm_op
        elif type(self.vm_op) is bytes:
            return ord(self.vm_op)
        else:
            raise Exception('Invalid op: %s ' % self.vm_op)

    def __init__(self, vm_op=None, pytoken=None,addr=None, data=None):
        self.vm_op = vm_op
        self.pytoken = pytoken
        self.addr = addr

        if self.pytoken is not None and hasattr(self.pytoken, 'data'):
            self.data = self.pytoken.data

        self.data = data


class VMTokenizer():

    method = None

    _address = None

    vm_tokens = None




    def __init__(self, method):
        self.method = method
        self._address = 0
        self.vm_tokens = {}

        self.method_begin_items()


    def to_s(self):

        lineno = self.method.start_line_no
        pstart = True
        for i, (key, value) in enumerate(self.vm_tokens.items()):

            if value.pytoken:
                pt = value.pytoken

                do_print_line_no = False
                to_label = None
                if pt.line_no != lineno:
                    print("\n")
                    lineno = pt.line_no
                    do_print_line_no = True


                if pt.args and type(pt.args) is Label:
                    addr = value.addr
                    plus_addr = int.from_bytes(value.data,'little')
                    target_addr = addr + plus_addr
                    to_label = 'to %s ' % target_addr

                lno = "{:<10}".format(pt.line_no if do_print_line_no or pstart else '')
                addr = "{:<4}".format(key)
                op = "{:<20}".format(str(pt.op_name))
                arg = "{:<50}".format(to_label if to_label is not None else pt.arg_s)

                print("%s%s%s%s" % (lno,addr,op,arg))

            pstart=False

    def to_b(self):
        b_array = bytearray()
        for key,vm_token in self.vm_tokens.items():

#            if vm_token.pytoken:
#                print("%s  -->  %s" % (vm_token.pytoken.py_op, vm_token.vm_op))
#            else:
#                print("%s  -->  %s" % (vm_token.pytoken, vm_token.vm_op))

            b_array.append(vm_token.out_op)

            if vm_token.data is not None:
#                print("DATA                 %s" % vm_token.data)
                b_array = b_array + vm_token.data

        return b_array


    def method_begin_items(self):

        #gotta start your day right with a nop ( actually i guess not)
#        pytoken = PyToken(pyop.NOP,lineno=self.method.start_line_no)
#        self.convert1(OpCode.NOP, pytoken)

        #we just need to inssert the total number of arguments + body variables
        #which is the length of the method `local_stores` dictionary
        #then create a new array for the vm to store
        total_items = self.method.total_lines + len(self.method.args)

        self.insert_push_integer(total_items)
        self.insert1(OpCode.NEWARRAY)
        self.insert1(OpCode.TOALTSTACK)

        for index, arg in enumerate(self.method.args):
            self.convert_load_parameter(arg, index)

    def insert_vm_token_at(self, vm_token, index):
        #print("INSERTING VM TOKEN AT %s %s " % (vm_token.vm_op, index))
        self.vm_tokens[index] = vm_token


    def insert1(self, vm_op, data=None):

        start_addr = self._address

        vmtoken = VMToken(vm_op=vm_op, addr=start_addr, data=data)

        self._address += 1

        if vmtoken.data is not None:

            self._address += len(vmtoken.data)


        self.insert_vm_token_at(vmtoken, vmtoken.addr)


        return vmtoken



    def insert_push_data(self, data):

        dlen = len(data)

        if dlen == 0:
            return self.insert1(OpCode.PUSH0)

        elif dlen <= 75:
            return self.insert1(dlen,data)

        if dlen < 0x100:
            prefixlen = 1
            code = OpCode.PUSHDATA1

        elif dlen < 0x1000:
            prefixlen = 2
            code = OpCode.PUSHDATA2

        else:
            prefixlen = 4
            code = OpCode.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return self.insert1(code,byts)

    def insert_push_integer(self, i):
        if i == 0:
            return self.insert1(OpCode.PUSH0)
        elif i == -1:
            return self.insert1(OpCode.PUSHM1)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            return self.insert1(out)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return self.insert_push_data(outdata)


    def convert1(self,vm_op, py_token=None, data=None):

        start_addr = self._address

        vmtoken = VMToken(vm_op=vm_op, addr=start_addr, pytoken=py_token,data=data)

        #here is where we will do something about
        #jump targets etc

        self._address += 1


        if vmtoken.data is not None and type(vmtoken.data) is not Label:

            self._address += len(data)

        self.insert_vm_token_at(vmtoken, start_addr)

        return vmtoken



    def convert_push_data(self, data, py_token=None):

        dlen = len(data)
        if dlen == 0:
            return self.convert1(OpCode.PUSH0, py_token=py_token)
        elif dlen <= 75:
            return self.convert1(len(data), py_token=py_token, data=data)

        if dlen < 0x100:
            prefixlen = 1
            code = OpCode.PUSHDATA1
        elif dlen < 0x1000:
            prefixlen = 2
            code = OpCode.PUSHDATA2
        else:
            prefixlen = 4
            code = OpCode.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return self.convert1(code,py_token=py_token,data=byts)


    def convert_push_integer(self, i, py_token=None):
        if i == 0:
            return self.convert1(OpCode.PUSH0, py_token=py_token)
        elif i == -1:
            return self.convert1(OpCode.PUSHM1, py_token=py_token)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            return self.convert1(out, py_token=py_token)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return self.convert_push_data(outdata, py_token=py_token)


    def convert_store_local(self, py_token):


        # set array
        self.convert1(OpCode.FROMALTSTACK, py_token=py_token)
        self.convert1(OpCode.DUP)
        self.convert1(OpCode.TOALTSTACK)

        local_name = py_token.args

        position = self.method.local_stores[local_name]

        print("POSITION FOR LOCAL NAME %s %s " % (local_name, position))

        # set i the index of the local variable to be stored
        self.convert_push_integer(position)

        # set item
        self.convert_push_integer(2)
        self.convert1(OpCode.ROLL)
        self.convert1(OpCode.SETITEM)

    def convert_load_local(self, py_token):

        local_name = py_token.args

        position = self.method.local_stores[local_name]

        # get array
        self.convert1(OpCode.FROMALTSTACK, py_token=py_token)
        self.convert1(OpCode.DUP)
        self.convert1(OpCode.TOALTSTACK)

        # get i?
        self.convert_push_integer(position)
        self.convert1(OpCode.PICKITEM)


    def convert_load_parameter(self, arg, position):

        length = len(self.method.local_stores)
        self.method.local_stores[arg] = length

        # get array
        self.insert1(OpCode.FROMALTSTACK)
        self.insert1(OpCode.DUP)
        self.insert1(OpCode.TOALTSTACK)

        self.insert_push_integer(position)
        self.insert_push_integer(2)

        self.insert1(OpCode.ROLL)
        self.insert1(OpCode.SETITEM)

