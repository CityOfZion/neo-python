
from byteplay3 import Opcode,Label
from boa.code.pytoken import PyToken
from boa.code import pyop

import pdb

class Block():

    forloop_counter = 0

    localmethod_counter = 0

    oplist = None # list

    _label = None # list


    iterable_variable = None
    iterable_loopcounter = None
    iterable_looplength = None
    iterable_item_name = None

    list_comp_iterable_variable = None
    list_comp_iterable_loopcounter = None
    list_comp_iterable_looplength = None
    list_comp_iterable_item_name = None

    slice_item_length = None

    has_dynamic_iterator = False

    local_func_name = None
    local_func_varname = None

    def __init__(self, operation_list):
        self.oplist = operation_list

        self.iterable_variable = None
        self.iterable_loopcounter = None
        self.iterable_looplength = None
        self.iterable_item_name = None

        self.list_comp_iterable_variable = None
        self.list_comp_iterable_loopcounter = None
        self.list_comp_iterable_looplength = None
        self.list_comp_iterable_item_name = None


        self.has_dynamic_iterator = False

        self.slice_item_length = None

    def __str__(self):
        if self._label:
            return '[Block] %s          [label] %s' % (self.oplist, self._label)
        return '[Block]: %s' % self.oplist


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
    def has_load_attr(self):
        for token in self.oplist:
            if token.py_op == pyop.LOAD_ATTR:
                return True
        return False

    @property
    def has_make_function(self):
        for token in self.oplist:
            if token.py_op == pyop.MAKE_FUNCTION:
                return True
        return False


    @property
    def has_slice(self):
        for token in self.oplist:
            if token.py_op == pyop.BUILD_SLICE:
                return True


    @property
    def is_return(self):
        if len(self.oplist):
            token = self.oplist[-1]
            if token.py_op == pyop.RETURN_VALUE:
                return True
        return False


    @property
    def is_iter(self):
        has_get_iter = False
        for token in self.oplist:
            if token.py_op == pyop.GET_ITER:
                has_get_iter = True
            elif token.py_op == pyop.MAKE_FUNCTION:
                return False
        return has_get_iter


    @property
    def iterable_local_vars(self):
        return [
            self.iterable_looplength,
            self.iterable_loopcounter,
            self.iterable_item_name,
        ]

    @property
    def list_comp_iterable_local_vars(self):
        return [
            self.list_comp_iterable_looplength,
            self.list_comp_iterable_loopcounter,
            self.list_comp_iterable_item_name,
            self.list_comp_iterable_variable,
        ]

    @property
    def has_unprocessed_method_calls(self):
        if self.has_slice:
            return False
#        if self.is_list_comprehension:
#            return False
        for token in self.oplist:
            if token.py_op == pyop.CALL_FUNCTION and token.func_processed == False:
                return True
        return False

    @property
    def has_unprocessed_array_sub(self):
        for token in self.oplist:
            if token.py_op == pyop.STORE_SUBSCR and token.array_processed == False:
                return True
        return False


    @property
    def has_unprocessed_array(self):
        for token in self.oplist:
            if token.py_op == pyop.BUILD_LIST and token.array_processed == False:
                return True
        return False


    @property
    def is_list_comprehension(self):
        if self.has_make_function:
            for token in self.oplist:
                if token.py_op == pyop.GET_ITER:
                    return True
        if self.list_comp_iterable_variable:
            return True

        return False


    def preprocess_load_attr(self, method):
        while self.has_load_attr:

            index_to_rep = -1
            new_call = None

            for index, token in enumerate(self.oplist):

                if token.py_op == pyop.LOAD_ATTR:

                    what_to_load = 'Get%s' % token.args

                    call_func = PyToken(Opcode(pyop.CALL_FUNCTION), lineno=self.line,index=-1, args=what_to_load)
                    call_func.func_processed = True
                    call_func.func_name = what_to_load
                    call_func.func_params = [self.oplist[index-1]]

                    index_to_rep = index
                    new_call = call_func

            if index_to_rep > -1 and new_call is not None:
                self.oplist[index_to_rep] = new_call
                del self.oplist[index_to_rep - 1]

    def preprocess_make_function(self, method):
        code_obj = self.oplist[0].args
        code_obj_name = self.oplist[1].args
        self.local_func_name = "%s_%s" % (code_obj_name, Block.localmethod_counter)
        Block.localmethod_counter += 1

        from boa.code.method import Method

        m = Method(code_object=code_obj,parent=method.parent, make_func_name=self.local_func_name)
        method.parent.add_method(m)

        self.local_func_varname = self.oplist[-1].args



    def preprocess_slice(self):
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
#                print("ENDOP: %s " % end_op.args)

                if end_op.args == None:
#                    print("END OP IS NONE, convert to function len call!")
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
            self.oplist = [getlength_token,slicelength_token] + self.oplist




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
        ld_counter_2 = PyToken(op= Opcode(pyop.LOAD_FAST), lineno=first_op.line_no,index=-1, args=setup_block.iterable_loopcounter)
        #load the constant 1
        increment_const = PyToken(op=Opcode(pyop.LOAD_CONST), lineno=first_op.line_no, index=-1, args=1)
        #add it to the counter
        increment_add = PyToken(op=Opcode(pyop.INPLACE_ADD), lineno=first_op.line_no, index=-1)
        #and store it again
        increment_store = PyToken(op=Opcode(pyop.STORE_FAST), lineno=first_op.line_no, index=-1, args=setup_block.iterable_loopcounter)

        self.oplist = [
                        ld_load_iterable,ld_counter,ld_subscript,st_iterable,

                        ld_counter_2, increment_const, increment_add, increment_store

                      ] + self.oplist



    def preprocess_method_calls(self, orig_method):

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

                    #we need to check if this is a method
                    #that is local to this block's method
                    for key, value in orig_method.local_methods.items():
                        if key == call_method_name:
                            call_method_name = value

                    token.func_params = params
                    token.func_name = call_method_name
                    token.func_type = call_method_type

                    changed_items = [token]

                    start_index_change = index - param_count - 1
                    end_index_change = index

            if start_index_change is not None and end_index_change is not None:
                tstart = self.oplist[0:start_index_change]
                tend = self.oplist[end_index_change+1:]
                self.oplist = tstart + changed_items + tend




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

        newitems = [PyToken(Opcode(pyop.NOP),self.line),
#                    PyToken(pyop.DROP_BODY, self.line),
                    PyToken(Opcode(pyop.FROMALTSTACK), self.line),
                    PyToken(Opcode(pyop.DROP), self.line)]

        self.oplist = tstart + newitems + tend




    def preprocess_list_comprehension(self, method):
        # at this point, the preprocess make function has
        # already done its thing on the block, so we're not interested in it

        self.oplist = self.oplist[3:]
#        items = self.oplist[3:]

        setup_loop = PyToken(op=Opcode(pyop.SETUP_LOOP),lineno=self.line,index=-1)

        # first we need to create a loop counter variable
        self.list_comp_iterable_loopcounter = 'list_comp_loop_counter_%s' % Block.forloop_counter

        # load the value 0
        loopcounter_start_ld_const = PyToken(op=Opcode(pyop.LOAD_CONST), lineno=self.line, index=-1, args=0)
        # now store the loop counter
        loopcounter_store_fast = PyToken(op=Opcode(pyop.STORE_FAST), lineno=self.line, index=-1,
                                         args=self.list_comp_iterable_loopcounter)

        # this loads the list that is going to be iterated over ( LOAD_FAST )
        # this will be removed... its added into the call get length token function params
        # unless this is a dynamic iteration, like for x in range(x,y)

        iterable_load = self.oplist[0]

        self.list_comp_iterable_item_name = iterable_load.args

        #the following is in the case that we're doing something like for i in range(x,y)
        dynamic_iterable_items = []
        if iterable_load.py_op == pyop.CALL_FUNCTION:
            self.has_dynamic_iterator = True
            self.iterable_item_name = 'forloop_dynamic_range_%s' % Block.forloop_counter
            dynamic_iterator_store_fast = PyToken(op=Opcode(pyop.STORE_FAST), lineno=self.line, index=-1,
                                                  args=self.iterable_item_name)
            # if we're calling a method in this for i in, like for i in range(x,y) then we need
            # to call the function
            dynamic_iterable_items = [iterable_load, dynamic_iterator_store_fast]


        # Now we need to get the length of that list, and store that as a local variable
        call_get_length_token = PyToken(op=Opcode(pyop.CALL_FUNCTION), lineno=self.line, args=1)
        call_get_length_token.func_processed = True
        call_get_length_token.func_params = [iterable_load]
        call_get_length_token.func_name = 'len'

        # now we need a variable name to store the length of the array
        self.list_comp_iterable_looplength = 'list_comp_loop_length_%s' % Block.forloop_counter

        # now store the variable which is the output of the len(items) call
        looplength_store_op = PyToken(op=Opcode(pyop.STORE_FAST), lineno=self.line, index=-1,
                                      args=self.list_comp_iterable_looplength)

        get_iter = self.oplist[1]

        for_iter_label = Label()
        jmp_if_false_label = Label()

        for_iter = PyToken(op=Opcode(pyop.FOR_ITER),lineno=self.line,index=-1)
        for_iter.jump_label = for_iter_label

        end_block = PyToken(op=Opcode(pyop.POP_BLOCK), lineno=self.line, index=-1)
        end_block.jump_label = jmp_if_false_label

        jmp_abs_back = PyToken(op=Opcode(pyop.JUMP_ABSOLUTE), lineno=self.line, index=-1, args=for_iter_label)

        self.list_comp_iterable_variable = 'list_comp_local_i_%s' % Block.forloop_counter


        ld_loopcounter = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=self.line, index=-1,
                                 args=self.list_comp_iterable_loopcounter)

        ld_loop_length = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=self.line, index=-1,
                                 args=self.list_comp_iterable_looplength)

        new__compare_op = PyToken(op=Opcode(pyop.COMPARE_OP), lineno=self.line, index=-1, args='<')
        new__popjump_op = PyToken(op=Opcode(pyop.POP_JUMP_IF_FALSE), lineno=self.line, index=-1,
                                  args=jmp_if_false_label)



        #ok now we do the loop block stuff here


        #
        # the following loads the iterated item into the block
        #

        # load the iterable collection
        ld_load_iterable = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=self.line, index=-1,
                                   args=self.list_comp_iterable_item_name)

        # load the counter var
        ld_counter = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=self.line, index=-1,
                             args=self.list_comp_iterable_loopcounter)

        # binary subscript of the iterable collection
        ld_subscript = PyToken(op=Opcode(pyop.BINARY_SUBSCR), lineno=self.line, index=-1)

        # now store the iterated item
        st_iterable = PyToken(op=Opcode(pyop.STORE_FAST), lineno=self.line, index=-1,
                              args=self.list_comp_iterable_variable)

        #
        # the following load the forloop counter and increments it
        #

        # load the counter var
        ld_counter_2 = PyToken(op=Opcode(pyop.LOAD_FAST), lineno=self.line, index=-1,
                             args=self.list_comp_iterable_loopcounter)
        # load the constant 1
        increment_const = PyToken(op=Opcode(pyop.LOAD_CONST), lineno=self.line, index=-1, args=1)
        # add it to the counter
        increment_add = PyToken(op=Opcode(pyop.INPLACE_ADD), lineno=self.line, index=-1)
        increment_add.func_processed = True
        # and store it again
        increment_store = PyToken(op=Opcode(pyop.STORE_FAST), lineno=self.line, index=-1,
                                  args=self.list_comp_iterable_loopcounter)


        # and now we call the function of the list-comprehension

        list_comp_call_func = PyToken(op=Opcode(pyop.CALL_FUNCTION), lineno=self.line, index=-1, args=1)
        list_comp_call_func.func_name = self.local_func_name
        list_comp_call_func.func_params = [self.list_comp_iterable_variable]

        self.oplist = [
            setup_loop,  # SETUP_LOOP

            get_iter,  # GET_ITER, keep this in for now


            # the following 4 ops set up the iterator

            loopcounter_start_ld_const,  # LOAD_CONST 0
            loopcounter_store_fast,  # STORE_FAST forloopcounter_X

            # dynamic load loop stuff would go here



            call_get_length_token,  # CALL_FUNCTION 1

            looplength_store_op,  # STORE_FAST forloop_length_X


            # these last 5 ops controls the operation of the loop

            for_iter,  # tihs is the jump target for the end of the loop execution block

            ld_loopcounter,  # load in the loop counter LOAD_FAST forloopcounter_X

            ld_loop_length,  # load in the loop length LOAD_FAST forloop_length_X

            new__compare_op,  # COMPARE_OP <, this will compare foorloop_counter_X < forloop_length_X

            new__popjump_op,  # POP_JUMP_IF_FALSE jumps to the loop exit when counter == length

            #the following are the loop body items
            ld_load_iterable,

            ld_counter,

            ld_subscript,

            st_iterable,

            ld_counter_2,

            increment_const,

            increment_add,
            increment_add, # this is a hack... when the list_comp_call_func is processed, it
                           # takes out a few things from the block
                           # so we add it in twice (blerg...) so it gets put back in
            increment_store,

            #put call method of the list comp here...
            list_comp_call_func,

            #now pop back to for_iter
            jmp_abs_back,

            end_block,
        ]

#        if len(dynamic_iterable_items):
#            self.oplist.insert(4, dynamic_iterable_items[0])
#            self.oplist.insert(5, dynamic_iterable_items[1])

        Block.forloop_counter += 1

