from boa.code import pyop

from byteplay3 import Label,isopcode,haslocal,Code

from opcode import opname

from boa.blockchain.vm import VMOp

from neo.BigInteger import BigInteger

from collections import OrderedDict

NEO_SC_FRAMEWORK='boa.blockchain.vm.'



class PyToken():

    py_op = None

    args = None

    line_no = None

    addr = None

    tokenizer = None

    jump_label = None

    array_processed = False

    array_item = None

    #method calling things

    func_processed = False

    func_params = None

    func_name = None
    func_type = None


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

    def __init__(self, op, lineno, index=None,args=None, array_item=None):

        self.py_op = op

        self.args = args

        self.line_no = lineno

        self.addr = index

        self.array_item = array_item


    def __str__(self):
        arg = ''

        if self.args:
            if type(self.args) is Label:
                arg = str(self.args)
            else:
                arg = self.args
            return '%s      %s   %s  --> %s ' % (self.line_no, self.addr, self.op_name, arg)
        return '%s      %s   %s' % (self.line_no, self.addr, self.op_name)


    def to_vm(self, tokenizer, prev_token=None):

        self.tokenizer = tokenizer
        token = None

        if self.is_op:



            op = self.py_op


            if op == pyop.NOP:
                token = tokenizer.convert1(VMOp.NOP, self)

            elif op == pyop.RETURN_VALUE:
                token = tokenizer.convert1(VMOp.RET, self)


            #control flow
            elif op == pyop.BR_S:
                token = tokenizer.convert1(VMOp.JMP, self, data=self.args)

            elif op == pyop.JUMP_FORWARD:
                token = tokenizer.convert1(VMOp.JMP,self, data=bytearray(2))

            elif op == pyop.JUMP_ABSOLUTE:
                token = tokenizer.convert1(VMOp.JMP,self, data=bytearray(2))

            elif op == pyop.POP_JUMP_IF_FALSE:
                token = tokenizer.convert1(VMOp.JMPIFNOT, self, data=bytearray(2))

            elif op == pyop.POP_JUMP_IF_TRUE:
                token = tokenizer.convert1(VMOp.JMPIF, self, data=bytearray(2))

            #loops
            elif op == pyop.SETUP_LOOP:
                token = tokenizer.convert1(VMOp.NOP, self)

            elif op == pyop.BREAK_LOOP:
                token = tokenizer.convert1(VMOp.JMP, self, data=bytearray(2))

            elif op == pyop.FOR_ITER:
                token = tokenizer.convert1(VMOp.NOP, self)

#            elif op == pyop.GET_ITER:
#                token = tokenizer.convert1(VMOp.NOP, self)

            elif op == pyop.POP_BLOCK:
                token = tokenizer.convert1(VMOp.NOP, self)



            elif op == pyop.FROMALTSTACK:
                token = tokenizer.convert1(VMOp.FROMALTSTACK, self)
            elif op == pyop.DROP:
                token = tokenizer.convert1(VMOp.DROP, self)

            #loading constants ( ie 1, 2 etc)
            elif op == pyop.LOAD_CONST:

                if type(self.args) is int:
                    token = tokenizer.convert_push_integer(self.args, self)
                elif type(self.args) is str:
                    str_bytes = self.args.encode('utf-8')
                    self.args = str_bytes
                    token = tokenizer.convert_push_data(self.args, self)
                elif type(self.args) is bytes:
                    token = tokenizer.convert_push_data(self.args, self)
                elif type(self.args) is bytearray:
                    token = tokenizer.convert_push_data(bytes(self.args), self)
                elif type(self.args) is bool:
                    token = tokenizer.convert_push_integer(self.args)
                elif type(self.args) == type(None):
                    token = tokenizer.convert_push_data(bytearray(0))
                elif type(self.args) == Code:
                    pass
                else:

                    raise Exception("Could not load type %s for item %s " % (type(self.args), self.args))

            #storing / loading local variables
            elif op == pyop.STORE_FAST:
                token = tokenizer.convert_store_local(self)

            elif op == pyop.LOAD_FAST:
                token = tokenizer.convert_load_local(self)


            #unary ops

#            elif op == pyop.UNARY_INVERT:
#                token = tokenizer.convert1(VMOp.INVERT, self)

            elif op == pyop.UNARY_NEGATIVE:
                token = tokenizer.convert1(VMOp.NEGATE, self)

            elif op == pyop.UNARY_NOT:
                token = tokenizer.convert1(VMOp.NOT, self)

#            elif op == pyop.UNARY_POSITIVE:
                #hmmm
#                token = tokenizer.convert1(VMOp.ABS, self)
#                pass

            #math
            elif op in [pyop.BINARY_ADD, pyop.INPLACE_ADD]:

#we can't tell by looking up the last token what type of item it was
#will need to figure out a different way of concatting strings
#                if prev_token and type(prev_token.args) is str:
#                    token = tokenizer.convert1(VMOp.CAT, self)
#                else:
                token = tokenizer.convert1(VMOp.ADD, self)

            elif op in [pyop.BINARY_SUBTRACT, pyop.INPLACE_SUBTRACT]:
                token = tokenizer.convert1(VMOp.SUB, self)

            elif op in [pyop.BINARY_MULTIPLY, pyop.INPLACE_MULTIPLY]:
                token = tokenizer.convert1(VMOp.MUL, self)

            elif op in [pyop.BINARY_FLOOR_DIVIDE, pyop.BINARY_TRUE_DIVIDE, pyop.INPLACE_FLOOR_DIVIDE, pyop.INPLACE_TRUE_DIVIDE]:
                token = tokenizer.convert1(VMOp.DIV, self)

            elif op in [pyop.BINARY_MODULO, pyop.INPLACE_MODULO]:
                token = tokenizer.convert1(VMOp.MOD, self)

            elif op == [pyop.BINARY_OR, pyop.INPLACE_OR]:
                token = tokenizer.convert1(VMOp.BOOLOR, self)

            elif op == [pyop.BINARY_AND, pyop.INPLACE_AND]:
                token = tokenizer.convert1(VMOp.BOOLAND, self)

            elif op == [pyop.BINARY_XOR, pyop.INPLACE_XOR]:
                token = tokenizer.convert1(VMOp.XOR, self)



            #compare

            elif op == pyop.COMPARE_OP:

                if self.args == '>':
                    token = tokenizer.convert1(VMOp.GT, self)
                elif self.args == '>=':
                    token = tokenizer.convert1(VMOp.GTE, self)
                elif self.args == '<':
                    token = tokenizer.convert1(VMOp.LT, self)
                elif self.args == '<=':
                    token = tokenizer.convert1(VMOp.LTE, self)
                elif self.args == '==':
                    token = tokenizer.convert1(VMOp.EQUAL, self)
                elif self.args == 'is':
                    token = tokenizer.convert1(VMOp.EQUAL, self)


            #arrays
            elif op == pyop.BUILD_LIST:
                token = tokenizer.convert_new_array(VMOp.NEWARRAY, self)
            elif op == pyop.SETITEM:
                token = tokenizer.convert_set_element(self, self.args)
#                token = tokenizer.convert1(VMOp.SETITEM,self, data=self.args)
            elif op == pyop.STORE_SUBSCR:
                #this wont occur because this op is preprocessed into a SETITEM op
                pass
            elif op == pyop.BINARY_SUBSCR:
                token = tokenizer.convert1(VMOp.PICKITEM,self)


            elif op == pyop.CALL_FUNCTION:

                token = tokenizer.convert_method_call(self)

        return token


class VMToken():

    addr = None

    pytoken = None

    data = None

    vm_op = None

    src_method = None

    target_method = None

    is_annotation = None

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

        self.src_method = None
        self.target_method = None

        self.is_annotation = False


class VMTokenizer():

    method = None

    _address = None

    vm_tokens = None




    def __init__(self, method):
        self.method = method
        self._address = 0
        self.vm_tokens = OrderedDict()

        self.method_begin_items()


    def to_s(self):

        lineno = self.method.start_line_no
        pstart = True
        for i, (key, value) in enumerate(self.vm_tokens.items()):

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
                        plus_addr = int.from_bytes(value.data,'little', signed=True)
                        target_addr = addr + plus_addr
                        to_label = 'to %s    [ %s ]' % (target_addr, pt.args)
                    else:
                        to_label = 'from << %s ' % pt.args
#                    to_label = 'to %s ' % pt.args
                elif pt.jump_label:
                    from_label = ' >> '
                    to_label ='from [%s]' % pt.jump_label

                lno = "{:<10}".format(pt.line_no if do_print_line_no or pstart else '')
                addr = "{:<4}".format(key)
                op = "{:<20}".format(str(pt.py_op))
                arg = "{:<50}".format(to_label if to_label is not None else pt.arg_s)

                print("%s%s%s%s%s" % (lno,from_label,addr,op,arg))

            pstart=False

    def to_b(self):
        b_array = bytearray()
        for key,vm_token in self.vm_tokens.items():

#            if vm_token.pytoken:
#                print("%s  -->  %s .... %s" % (vm_token.pytoken.py_op, vm_token.vm_op, vm_token.out_op))
#            else:
#                print("%s  -->  %s" % (vm_token.pytoken, vm_token.vm_op))

            b_array.append(vm_token.out_op)

            if vm_token.data is not None and vm_token.vm_op != VMOp.NOP:
                b_array = b_array + vm_token.data

        return b_array


    def method_begin_items(self):

        #gotta start your day right with a nop ( actually i guess not)
#        pytoken = PyToken(pyop.NOP,lineno=self.method.start_line_no)
#        self.convert1(VMOp.NOP, pytoken)

        #we just need to inssert the total number of arguments + body variables
        #which is the length of the method `local_stores` dictionary
        #then create a new array for the vm to store
        total_items = self.method.total_lines + len(self.method.args)

        self.insert_push_integer(total_items)
        self.insert1(VMOp.NEWARRAY)
        self.insert1(VMOp.TOALTSTACK)

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
            return self.insert1(VMOp.PUSH0)

        elif dlen <= 75:
            return self.insert1(dlen,data)

        if dlen < 0x100:
            prefixlen = 1
            code = VMOp.PUSHDATA1

        elif dlen < 0x1000:
            prefixlen = 2
            code = VMOp.PUSHDATA2

        else:
            prefixlen = 4
            code = VMOp.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return self.insert1(code,byts)

    def insert_push_integer(self, i):
        if i == 0:
            return self.insert1(VMOp.PUSH0)
        elif i == -1:
            return self.insert1(VMOp.PUSHM1)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            return self.insert1(out)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return self.insert_push_data(outdata)


    def convert1(self,vm_op, py_token=None, data=None):

        start_addr = self._address

        vmtoken = VMToken(vm_op=vm_op, addr=start_addr, pytoken=py_token,data=data)

        self._address += 1

        if vmtoken.data is not None and type(vmtoken.data) is not Label:
            self._address += len(data)

        self.insert_vm_token_at(vmtoken, start_addr)

        return vmtoken


    def convert_new_array(self, vm_op, py_token=None,data=None):

        #push the length of the array
        if type(py_token.args) is int:

            self.insert_push_integer(py_token.args)
        else:
            self.convert_load_local(py_token, py_token.args)

        self.convert1(VMOp.NEWARRAY,py_token)


    def convert_push_data(self, data, py_token=None):

        dlen = len(data)
        if dlen == 0:
            return self.convert1(VMOp.PUSH0, py_token=py_token)
        elif dlen <= 75:
            return self.convert1(len(data), py_token=py_token, data=data)

        if dlen < 0x100:
            prefixlen = 1
            code = VMOp.PUSHDATA1
        elif dlen < 0x1000:
            prefixlen = 2
            code = VMOp.PUSHDATA2
        else:
            prefixlen = 4
            code = VMOp.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return self.convert1(code,py_token=py_token,data=byts)


    def convert_push_integer(self, i, py_token=None):
        if i == 0:
            return self.convert1(VMOp.PUSH0, py_token=py_token)
        elif i == -1:
            return self.convert1(VMOp.PUSHM1, py_token=py_token)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            return self.convert1(out, py_token=py_token)

        bigint = BigInteger(i)

        outdata = bigint.ToByteArray()

        return self.convert_push_data(outdata, py_token=py_token)


    def convert_store_local(self, py_token):


        # set array
        self.convert1(VMOp.FROMALTSTACK, py_token=py_token)
        self.convert1(VMOp.DUP)
        self.convert1(VMOp.TOALTSTACK)

        local_name = py_token.args

        position = self.method.local_stores[local_name]

        # set i the index of the local variable to be stored
        self.convert_push_integer(position)

        # set item
        self.convert_push_integer(2)
        self.convert1(VMOp.ROLL)
        self.convert1(VMOp.SETITEM)

    def convert_load_local(self, py_token, name=None):

        if name is not None:
            local_name = name
        else:
            local_name = py_token.args

        position = self.method.local_stores[local_name]

        # get array
        self.convert1(VMOp.FROMALTSTACK, py_token=py_token)
        self.convert1(VMOp.DUP)
        self.convert1(VMOp.TOALTSTACK)

        # get i
        self.convert_push_integer(position)
        self.convert1(VMOp.PICKITEM)


    def insert_unknown_type(self, item):
        if type(item) is int:
            self.insert_push_integer(item)

        elif type(item) is str:
            str_bytes = item.encode('utf-8')
            self.insert_push_data(str_bytes)

        elif type(item) is bytearray:
            self.insert_push_data(bytes(item))

        elif type(item) is bytes:
            self.insert_push_data(item)

        elif type(item) is bool:
            self.insert_push_data(item)
        elif type(item) == type(None):
            self.insert_push_data(bytearray(0))
        else:
            raise Exception("Could not load type %s for item %s " % (type(item), item))

    def convert_set_element(self, arg, position):

#        print("converting set element %s %s" % (position, type(position)))

        if type(position) is int:

            self.insert_push_integer(position)
        elif type(position) is str:
            self.convert_load_local(None, name=position)

        if type(arg.array_item) is str:
            self.convert_load_local(None, name=arg.array_item)
        else:
            self.insert_unknown_type(arg.array_item)

        self.convert1(VMOp.SETITEM,arg)

    def convert_load_parameter(self, arg, position):

        length = len(self.method.local_stores)
        self.method.local_stores[arg] = length

        # get array
        self.insert1(VMOp.FROMALTSTACK)
        self.insert1(VMOp.DUP)
        self.insert1(VMOp.TOALTSTACK)

        self.insert_push_integer(position)
        self.insert_push_integer(2)

        self.insert1(VMOp.ROLL)
        self.insert1(VMOp.SETITEM)


    def convert_built_in_list(self, pytoken):
        new_array_len = 0
        lenfound = False
        for index,token in enumerate(pytoken.func_params):
            if token.args=='length' and not lenfound:
                new_array_len = pytoken.func_params[index + 1].args
                lenfound=True
        pytoken.args = new_array_len
        self.convert_new_array(VMOp.NEWARRAY, pytoken)


    def convert_method_call(self, pytoken):

        #special case for list initialization
        if pytoken.func_name == 'list':
            return self.convert_built_in_list(pytoken)


        for t in pytoken.func_params:
            t.to_vm(self)

        param_len = len(pytoken.func_params)

        if param_len <= 1:
            pass
        elif param_len == 2:
            self.insert1(VMOp.SWAP)
        elif param_len == 3:
            self.insert_push_integer(2)
            self.insert1(VMOp.XSWAP)
        else:
            half_p = int(param_len/2)

            for i in range(0, half_p):

                save_to = param_len - 1 - i

                self.insert_push_integer(save_to)
                self.insert1(VMOp.PICK)

                self.insert_push_integer(i + 1)
                self.insert1(VMOp.PICK)

                self.insert_push_integer(save_to + 2)
                self.insert1(VMOp.XSWAP)
                self.insert1(VMOp.DROP)

                self.insert_push_integer(i + 1)
                self.insert1(VMOp.XSWAP)
                self.insert1(VMOp.DROP)


        self.insert1(VMOp.NOP)


        fname = pytoken.func_name
        full_name = None
        for m in self.method.module.methods:
            if fname == m.name:
                full_name = m.full_name
#            print("all module method %s %s " % (m.name, m.full_name))


        #operational call like len(items) or abs(value)
        if self.is_op_call(fname):
            vmtoken = self.convert_op_call(fname, pytoken)

        #used for runtime.notify
        elif self.is_notify_call(fname):
            vmtoken = self.convert_notify_call(fname, pytoken)

        elif self.is_sys_call(full_name):
            vmtoken = self.convert_sys_call(full_name, pytoken)

        #used for python specific built in methods like `enumerate` or `tuple`
        elif self.is_built_in(fname):
            vmtoken = self.convert_built_in(fname, pytoken)

        #otherwise we assume the method is defined by the module
        else:
            vmtoken = self.convert1(VMOp.CALL,py_token=pytoken,data=bytearray(b'\x05\x00'))

            vmtoken.src_method = self.method
            vmtoken.target_method = pytoken.func_name

        return vmtoken


    def is_op_call(self, op):

        if op in ['len','abs','min','max',]:
            return True
        return False

    def convert_op_call(self, op, pytoken=None):

        if op == 'len':
            return self.convert1(VMOp.ARRAYSIZE, pytoken)
        elif op == 'abs':
            return self.convert1(VMOp.ABS, pytoken)
        elif op == 'min':
            return self.convert1(VMOp.MIN,pytoken)
        elif op == 'max':
            return self.convert1(VMOp.MAX,pytoken)
        return None

    def is_notify_call(self, op):
        return False

    def convert_notify_call(self, op, pytoken=None):
        raise NotImplementedError()

    def is_sys_call(self, op):
        if op is not None and NEO_SC_FRAMEWORK in op:
            return True
        return False

    def convert_sys_call(self,op, pytoken=None):

        syscall_name = op.replace(NEO_SC_FRAMEWORK,'').encode('utf-8')
        length = len(syscall_name)
        ba = bytearray([length]) + bytearray(syscall_name)
        pytoken.is_sys_call=False
        vmtoken = self.convert1(VMOp.SYSCALL, pytoken, data=ba)
        self.insert1(VMOp.NOP)
        return vmtoken

    def is_built_in(self, op):

        if op in ['zip','type','tuple','super','str','slice',
                  'set','reversed','property','memoryview',
                  'map','list','frozenset','float','filter',
                  'enumerate','dict','divmod','complex','bytes','bytearray','bool',
                  'int','vars','sum','sorted','round','setattr','getattr',
                  'rep','quit','print','pow','ord','oct','next','locals','license',
                  'iter','isinstance','issubclass','input','id','hex',
                  'help','hash','hasattr','globals','format','exit',
                  'exec','eval','dir','deleteattr','credits','copyright',
                  'compile','chr','callable','bin','ascii','any','all',]:

            return True

        return False

    def convert_built_in(self, op, pytoken):

        if op == 'print':
            syscall_name = 'Neo.Runtime.Log'.encode('utf-8')
            length = len(syscall_name)
            ba = bytearray([length]) + bytearray(syscall_name)
#            pytoken.is_sys_call = True
            vmtoken = self.convert1(VMOp.SYSCALL, pytoken, data=ba)
            self.insert1(VMOp.NOP)
            return vmtoken

        raise NotImplementedError("[Compilation error] Built in %s is not implemented" % op)


#    def is_method_call(self, op):
#        if op in self