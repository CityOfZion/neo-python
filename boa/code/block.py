
from byteplay3 import Opcode
from boa.code.token import PyToken
from boa.code import pyop


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

            start_index_change = None
            end_index_change = None
            changed_items = None

            for index, token in enumerate(self.oplist):
                if token.py_op == pyop.BUILD_LIST and token.array_processed == False:

                    num_list_items = token.args

                    token.array_processed = True

                    if num_list_items > 0:
                        array_items = self.oplist[index-num_list_items:num_list_items]

                        start_index_change =index - num_list_items
                        end_index_change = index

                        changed_items = []
                        changed_items.append(token)

                        #this is the store fast op
                        next_token = self.oplist[index + 1]
                        changed_items.append(next_token)

                        #now we load  the new array
                        array_name = next_token.args

                        for index, item in enumerate(array_items):
                            #load the array to set the item into
                            ld_op = PyToken(Opcode(pyop.LOAD_FAST), token.line_no, args=array_name)
                            changed_items.append(ld_op)
                            #set the item into the array
                            settoken = PyToken(Opcode(pyop.SETITEM), token.line_no, args=index, array_item =item.args)
                            changed_items.append(settoken)

            if start_index_change is not None and end_index_change is not None:

                tstart = self.oplist[0:start_index_change]
                tend = self.oplist[end_index_change+2:]
                self.oplist = tstart + changed_items + tend


    def mark_as_end(self):

        tstart = self.oplist[:-1]
        tend = self.oplist[-1:]

        newitems = [PyToken(pyop.NOP,self.line), PyToken(pyop.FROMALTSTACK, self.line), PyToken(pyop.DROP, self.line)]

        self.oplist = tstart + newitems + tend


    def __str__(self):
        if self._label:
            return '[Block] %s          [label] %s' % (self.oplist, self._label)
        return '[Block]: %s' % self.oplist

