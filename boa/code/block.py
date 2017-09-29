
from byteplay3 import Opcode
from boa.code.token import PyToken
from boa.code import pyop

import pdb
class Block():

    forloop_counter = 0



    oplist = None # list

    _label = None # list


    iterable_variable = None
    iterable_loopcounter = None
    iterable_looplength = None
    iterable_item_name = None
    slice_item_length = None

    has_dynamic_iterator = False

    def __init__(self, operation_list):
        self.oplist = operation_list

        self.iterable_variable = None
        self.iterable_loopcounter = None
        self.iterable_looplength = None
        self.iterable_item_name = None
        self.has_dynamic_iterator = False

        self.slice_item_length = None

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
    def has_slice(self):
        for token in self.oplist:
            if token.py_op == pyop.BUILD_SLICE:
                return True

    def preprocess_slice(self):
        print("TOTAL OPLIST: %s " % len(self.oplist))
        index_to_remove=-1
        do_calculate_item_length = False
        getlength_token=None
        slicelength_token = None
        for index, token in enumerate(self.oplist):
            if token.py_op == pyop.BUILD_SLICE:
                #first, we want to take out the BINARY_SUBSC op, since we wont need it
                index_to_remove = index + 1

                #now we want to check the second item, for example item[2:4], we need to check 4
                #if you do item[2:], in python, normally the end is inferred
                #but we get None.
                #in that case, we need to convert None into the length of the item being sliced
                end_op = self.oplist[index-1]
                print("ENDOP: %s " % end_op.args)

                if end_op.args == None:
                    print("END OP IS NONE, convert to function len call!")
                    do_calculate_item_length = True
                    getlength_token = PyToken(op=Opcode(pyop.CALL_FUNCTION), lineno=token.line_no, args=1)
                    getlength_token.func_params = [self.oplist[0]]
                    getlength_token.func_name = 'len'

                    # now we need a variable name to store the length of the array
                    self.slice_item_length = 'sliceitem_length_%s' % Block.forloop_counter

                    # now store the variable which is the output of the len(items) call
                    slicelength_token = PyToken(op=Opcode(pyop.STORE_FAST), lineno=token.line_no, index=-1,
                                                  args=self.slice_item_length)

                    end_op.py_op = Opcode(pyop.LOAD_FAST)
                    end_op.args = self.slice_item_length

        if index_to_remove > -1:
            del self.oplist[index_to_remove]

        if do_calculate_item_length:
            print("DO CALCULATE!!!")
            self.oplist = [getlength_token,slicelength_token] + self.oplist

        print("TOTAL OPLIST: %s " % len(self.oplist))

    @property
    def is_return(self):
        if len(self.oplist):
            token = self.oplist[-1]
            if token.py_op == pyop.RETURN_VALUE:
                return True
        return False


    @property
    def is_iter(self):
        for token in self.oplist:
            if token.py_op == pyop.GET_ITER:
                return True
        return False

    @property
    def iterable_local_vars(self):
        return [
            self.iterable_looplength,
            self.iterable_loopcounter,
            self.iterable_item_name,
        ]

    def preprocess_iter(self):

        #in a better world this would be done in a more efficient way
        #for now this is kept to be as understandable as possible


        loopsetup = self.oplist[0]
        loopsetup.args = None
        loopsetup.jump_label = None

        #first we need to create a loop counter variable
        self.iterable_loopcounter = 'forloop_counter_%s' % Block.forloop_counter

        #load the value 0
        loopcounter_start_ld_const = PyToken(op=Opcode(pyop.LOAD_CONST),lineno=loopsetup.line_no,index=-1,args=0)
        #now store the loop counter
        loopcounter_store_fast = PyToken(op=Opcode(pyop.STORE_FAST), lineno=loopsetup.line_no, index=-1, args=self.iterable_loopcounter)


        #this loads the list that is going to be iterated over ( LOAD_FAST )
        # this will be removed... its added into the call get length token function params
        # unless this is a dynamic iteration, like for x in range(x,y)
        dynamic_iterable_items = []

        iterable_load = self.oplist[1]

        self.iterable_item_name = iterable_load.args

        if iterable_load.py_op == pyop.CALL_FUNCTION:

            self.has_dynamic_iterator = True

            self.iterable_item_name = 'forloop_dynamic_range_%s' % Block.forloop_counter

            dynamic_iterator_store_fast = PyToken(op=Opcode(pyop.STORE_FAST), lineno=loopsetup.line_no, index=-1,
                                             args=self.iterable_item_name)

            #if we're calling a method in this for i in, like for i in range(x,y) then we need
            #to call the function
            dynamic_iterable_items = [iterable_load, dynamic_iterator_store_fast]


        # Now we need to get the length of that list, and store that as a local variable

        call_get_length_token = PyToken(op = Opcode(pyop.CALL_FUNCTION),lineno=loopsetup.line_no, args=1)
        call_get_length_token.func_params = [iterable_load]
        call_get_length_token.func_name = 'len'

        #now we need a variable name to store the length of the array
        self.iterable_looplength = 'forloop_length_%s' % Block.forloop_counter

        #now store the variable which is the output of the len(items) call
        looplength_store_op = PyToken(op=Opcode(pyop.STORE_FAST),lineno=loopsetup.line_no,index=-1, args=self.iterable_looplength)

        get_iter = self.oplist[2]
        for_iter = self.oplist[3]

        store_iterable_name = self.oplist[4]

        self.iterable_variable = store_iterable_name.args # set the iterable variable name ( for example, i ) so that the loop body can use it


        ld_loopcounter = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=loopsetup.line_no, index=-1, args=self.iterable_loopcounter)

        ld_loop_length = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=loopsetup.line_no, index=-1, args=self.iterable_looplength)

        new__compare_op = PyToken(op = Opcode(pyop.COMPARE_OP),lineno=loopsetup.line_no, index=-1,args='<')
        new__popjump_op = PyToken(op = Opcode(pyop.POP_JUMP_IF_FALSE), lineno= loopsetup.line_no, index=-1, args=for_iter.args)

        for_iter.args = None

        self.oplist = [
            loopsetup, #SETUP_LOOP

            get_iter, #GET_ITER, keep this in for now


            #the following 4 ops set up the iterator

            loopcounter_start_ld_const, # LOAD_CONST 0
            loopcounter_store_fast, # STORE_FAST forloopcounter_X

            #dynamic load loop stuff would go here

            call_get_length_token, # CALL_FUNCTION 1

            looplength_store_op, # STORE_FAST forloop_length_X


            #these last 5 ops controls the operation of the loop

            for_iter, # tihs is the jump target for the end of the loop execution block

            ld_loopcounter, # load in the loop counter LOAD_FAST forloopcounter_X

            ld_loop_length, # load in the loop length LOAD_FAST forloop_length_X

            new__compare_op, # COMPARE_OP <, this will compare foorloop_counter_X < forloop_length_X

            new__popjump_op # POP_JUMP_IF_FALSE jumps to the loop exit when counter == length
        ]


        if len(dynamic_iterable_items):
            self.oplist.insert(4,dynamic_iterable_items[0])
            self.oplist.insert(5,dynamic_iterable_items[1])

        Block.forloop_counter += 1

    def process_iter_body(self, setup_block):

        first_op = self.oplist[0]

        #
        # the following loads the iterated item into the block
        #

        #load the iterable collection
        ld_load_iterable = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=first_op.line_no, index=-1, args=setup_block.iterable_item_name)

        #load the counter var
        ld_counter = PyToken(op= Opcode(pyop.LOAD_FAST), lineno=first_op.line_no,index=-1, args=setup_block.iterable_loopcounter)

        #binary subscript of the iterable collection
        ld_subscript = PyToken(op = Opcode(pyop.BINARY_SUBSCR), lineno=first_op.line_no, index=-1)

        #now store the iterated item
        st_iterable = PyToken(op = Opcode(pyop.STORE_FAST), lineno=first_op.line_no, index=-1, args=setup_block.iterable_variable)

        #
        # the following load the forloop counter and increments it
        #

        #load the counter var
        ld_counter = PyToken(op= Opcode(pyop.LOAD_FAST), lineno=first_op.line_no,index=-1, args=setup_block.iterable_loopcounter)
        #load the constant 1
        increment_const = PyToken(op=Opcode(pyop.LOAD_CONST), lineno=first_op.line_no, index=-1, args=1)
        #add it to the counter
        increment_add = PyToken(op=Opcode(pyop.INPLACE_ADD), lineno=first_op.line_no, index=-1)
        #and store it again
        increment_store = PyToken(op=Opcode(pyop.STORE_FAST), lineno=first_op.line_no, index=-1, args=setup_block.iterable_loopcounter)

        self.oplist = [
                        ld_load_iterable,ld_counter,ld_subscript,st_iterable,

                        ld_counter, increment_const, increment_add, increment_store

                      ] + self.oplist


    @property
    def has_unprocessed_method_calls(self):
        if self.has_slice:
            return False
        for token in self.oplist:
            if token.py_op == pyop.CALL_FUNCTION and token.func_processed == False:
                return True
        return False


    def preprocess_method_calls(self):

        while self.has_unprocessed_method_calls:
            start_index_change = None
            end_index_change = None
            changed_items = None

            for index, token in enumerate(self.oplist):
                if token.py_op == pyop.CALL_FUNCTION and token.func_processed == False:

                    token.func_processed = True
                    param_count = token.args

                    #why would param count be 256 when calling w/ kwargs?
                    #when keyword args are sent, the param count is 256 * num paramms?
                    if param_count % 256 == 0:
                        param_count = 2 * int(param_count / 256)

                    params = self.oplist[index-param_count:index]

                    call_method_op = self.oplist[index-param_count-1]

                    call_method_type = call_method_op.py_op
                    call_method_name = call_method_op.args

                    token.func_params = params
                    token.func_name = call_method_name
                    token.func_type = call_method_type
#                    pdb.set_trace()
                    changed_items = [token]

                    start_index_change = index - param_count - 1
                    end_index_change = index

            if start_index_change is not None and end_index_change is not None:
                tstart = self.oplist[0:start_index_change]
                tend = self.oplist[end_index_change+1:]
                self.oplist = tstart + changed_items + tend



    @property
    def has_unprocessed_array_sub(self):
        for token in self.oplist:
            if token.py_op == pyop.STORE_SUBSCR and token.array_processed == False:
                return True
        return False

    def preprocess_array_subs(self):
        while self.has_unprocessed_array_sub:
            start_index_change = None
            end_index_change = None
            changed_items = None

            for index, token in enumerate(self.oplist):
                if token.py_op == pyop.STORE_SUBSCR and token.array_processed == False:
                    token.array_processed = True
                    start_index_change = index -3
                    end_index_change = index

                    item_to_sub = self.oplist[index-3].args
                    array_to_sub = self.oplist[index-2].args
                    index_to_sub_at = self.oplist[index-1].args
                    changed_items = []

                    # load the array to set the item into
                    ld_op = PyToken(Opcode(pyop.LOAD_FAST), token.line_no, args=array_to_sub)
                    changed_items.append(ld_op)

                    #create the setitem op
                    settoken = PyToken(Opcode(pyop.SETITEM), token.line_no, args=index_to_sub_at, array_item=item_to_sub)
                    changed_items.append(settoken)

            if start_index_change is not None and end_index_change is not None:
                tstart = self.oplist[0:start_index_change]
                tend = self.oplist[end_index_change + 2:]
                self.oplist = tstart + changed_items + tend


    @property
    def has_unprocessed_array(self):
        for token in self.oplist:
            if token.py_op == pyop.BUILD_LIST and token.array_processed == False:
                return True
        return False

    def preprocess_arrays(self):

        while self.has_unprocessed_array:

            blist_start_index = None
            blist_end_index = None
            array_items = []
            for index, token in enumerate(self.oplist):
                if token.py_op == pyop.BUILD_LIST and token.array_processed == False and blist_start_index == None:

                    num_list_items = token.args
                    blist_start_index = index - num_list_items
                    blist_end_index = index
                    array_items = self.oplist[index - num_list_items:num_list_items]
                    array_items.reverse()

                    token.array_processed = True

            if blist_start_index is not None:
                self.oplist = self.oplist[0:blist_start_index] + array_items + self.oplist[blist_end_index:]



    def mark_as_end(self):

        tstart = self.oplist[:-1]
        tend = self.oplist[-1:]

        newitems = [PyToken(pyop.NOP,self.line), PyToken(pyop.FROMALTSTACK, self.line), PyToken(pyop.DROP, self.line)]

        self.oplist = tstart + newitems + tend


    def __str__(self):
        if self._label:
            return '[Block] %s          [label] %s' % (self.oplist, self._label)
        return '[Block]: %s' % self.oplist

