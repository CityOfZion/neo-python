from boa.Node.ASTNode import ASTNode
from boa.Node.BodyNode import BodyNode
from boa.Token.NeoToken import NeoToken,TokenConverter,Nop,BRFalse,BRTrue
from boa.Compiler import Compiler
from neo.VM import OpCode
import pdb

from _ast import FunctionDef,Return,Assign,\
    AugAssign,Load,Store,Name,Break,BinOp,Num,Str,\
    NameConstant,Ellipsis,Dict,List,Tuple,Set,Bytes, \
    Add,Sub,Mult,Div,FloorDiv,Mod,Pow,LShift,RShift, \
    BitAnd,BitOr,BitXor, Compare, IfExp, If


TERMINAL_ITEMS = [
    Num,Str,Ellipsis,Dict,List,Tuple,Set,Bytes,Name,NameConstant,
]

NAME_ITEMS = [
    Name, NameConstant,
]

BR_TRUE = 'BR_True'
BR_FALSE = 'BR_False'


import pprint
class FunctionNode(ASTNode):

    _name = None

    _decorators = None

    _items = None


    _arguments = None
    _argument_types = None

    _return_type = None

    _classref = None


    _BodyTokens = None

    _store_table = None

    _duplicateAssigns = None

    @property
    def StoreTable(self):
        return self._store_table


    @property
    def BodyTokens(self):
        return self._BodyTokens

    @BodyTokens.setter
    def BodyTokens(self, value):

        self._BodyTokens = value

    def InsertBodyToken(self, token, addr ):

#        print("SETTING ITEM %s at index %s " % (token, addr))
        try:
            self.BodyTokens[addr] = token
            return True
        except Exception as e:
            print("could not insert body token %s " % e)

        return False

    @property
    def Class(self):
        return self._classref

    @property
    def IsEntry(self):
        return self._name == 'Main'

    @property
    def name(self):
        return self._name


    @property
    def bodyNodes(self):
        return self._items

    @property
    def arguments(self):
        return self._arguments


    @property
    def duplicateAssigns(self):
        return self._duplicateAssigns


    def __init__(self, node):

        self._type = FunctionDef
        self._decorators = []
        self._items = []
        self._arguments = []

        self._BodyTokens = {}

        self._store_table = {}

        super(FunctionNode, self).__init__(node)



    def _build(self):
        super(FunctionNode, self)._build()

        self._name = self._node.name

        if self._name=='Main':
            Compiler.Instance().RegisterEntry(self)

        self._decorators = [item.id for item in self._node.decorator_list]

        self._arguments = [arg.arg for arg in self.Node.args.args]

        try:
            self._argument_types = [arg.annotation.id for arg in self.Node.args.args]
        except Exception as e:
            pass

        try:
            self._return_type = self.Node.returns.id
        except Exception as e:
            self._return_type = None


        index=0

        nop = BodyNode(Nop(),0)
        self._items.append(nop)

        has_returned = False

        for item in self.Node.body:


            if type(item) is Return:
                has_returned = True

            self._build_item(item, index)


            index += 1

        if not has_returned:
            # we need a nop first befor return
            nopval = BodyNode(Nop(), index)
            self._items.append(nopval)

            retval = BodyNode(Return(), index)
            self._items.append(retval)


        for offset, item in enumerate(self._items):
            item.offset = offset
            print("---------------------------Created item %s" % item.AddrOffset())



        Compiler.Instance().RegisterMethod(self)



    def Convert(self):


        compiler = Compiler.Instance()
        compiler.TokenAddr = 0
        compiler.AddrConv = {}

        self._insert_begin()

        skipcount = 0

        has_returned=False

        for item in self._items:

            if skipcount > 0:
                skipcount -=1

            else:

                if item.type == Return:
                    self._insert_end(item)

                skipcount = TokenConverter._ConvertCode(item, self)



        self._convert_addr_in_method()

    def _insert_begin(self):

        varcount = len(self._arguments) + self._collapse_body()
        TokenConverter._InsertPushInteger(varcount, "begincode", self)
        TokenConverter._Insert1(OpCode.NEWARRAY, "", self)
        TokenConverter._Insert1(OpCode.TOALTSTACK, "", self)


        for i in range(0, len(self._arguments)):

            arg = self._arguments[i]
            print("INSERTING ARGUMENT ! %s" % (arg))

            TokenConverter._Insert1(OpCode.FROMALTSTACK, "set param %s" % i, self)
            TokenConverter._Insert1(OpCode.DUP, "", self)
            TokenConverter._Insert1(OpCode.TOALTSTACK, "", self)

            TokenConverter._InsertPushInteger(i, "", self)
            TokenConverter._InsertPushInteger(2, "", self)
            TokenConverter._Insert1(OpCode.ROLL, "", self)
            TokenConverter._Insert1(OpCode.SETITEM, "", self)


    def _collapse_body(self):
        count = 0
        assigns = []
        self._duplicateAssigns = []

        for n in self._node.body:
            if type(n) is Assign:
                if not n.targets[0].id in assigns:
                    assigns.append(n.targets[0].id)
                    count +=1
                else:
                    self._duplicateAssigns.append(n.targets[0].id)
            else:
                count += 1

        return count

    def _convert_addr_in_method(self):

        compiler = Compiler.Instance()

        for key, c in self._BodyTokens.items():

            if c.needfix and c.code != OpCode.CALL:
                pprint.pprint(compiler.AddrConv)
                addr = compiler.AddrConv[c.offset + 1]
                addr_off = addr - c.addr
                c.byts = addr_off.to_bytes(2,'little')
                c.needfix = False

    def _insert_end(self, src=None):

        TokenConverter._Insert1(OpCode.FROMALTSTACK, "endcode", self)
        TokenConverter._Insert1(OpCode.DROP, "", self)


    def Validate(self):

        return super(FunctionNode, self).Validate()


    def __str__(self):

        return "[Function Node] %s " % self._name



    def _expand_item(self, item, index, tostore=None, store=True):

        print("EXPANDING ITEM %s %s" % (type(item), tostore))
        if type(item) in NAME_ITEMS and not store:
            pushval = BodyNode(item, index)
            self._items.append(pushval)

        elif type(item) in TERMINAL_ITEMS:
            # push the value of the item to be returned
            pushval = BodyNode(item, index)
            self._items.append(pushval)

            # now store the value of the item to be returned
            val = tostore

            if not val:
                val = Name()
                val.ctx = Store()
                if type(item) is Name:
                    val.id = item.id
                else:
                    val.id = None

            storeval = BodyNode(val, index)
            self._items.append(storeval)

        else:

            self._build_item(item, index)

            # now store the value of the item to be returned

            if store:
                val = tostore

                if not val:
                    val = Name()
                    val.ctx = Store()
                    if type(item) is Name:
                        val.id = item.id
                    else:
                        val.id = None

                storeval = BodyNode(val, index)
                self._items.append(storeval)

    def _build_item(self, item, index):

        print("PARSING ITEM %s " % (type(item)))
        if type(item) in [Assign, AugAssign]:
            print("WILL ASSIGN ITEMeeeeeee %s %s %s" % (item.value, item.targets[0], len(item.targets)))
            self._expand_item(item.value, index, item.targets[0])

        elif type(item) is Return:
            print("WILL EXPAND RETURN!!!!!.... %s " % (vars(item)))

            if getattr(item, 'value',None) is not None:

                self._expand_item(item.value, index)


            br_type = getattr(item, 'br_type',None)


            if br_type is None:
                breakval = BodyNode(Break(), index)

                # now we indicate an exit
                self._items.append(breakval)


                # and then load the value
                val = Name()
                val.ctx = Load()
                val.id = None
                loadval = BodyNode(val, index)
                self._items.append(loadval)

                # we need a nop first befor return
                nopval = BodyNode(Nop(), index)
                self._items.append(nopval)


                retval = BodyNode(item, index)
                self._items.append(retval)

            elif br_type == BR_TRUE:

                retval = BodyNode(BRTrue(), index)
                self._items.append(retval)

                nopval = BodyNode(Nop(), index)
                self._items.append(nopval)

            elif br_type == BR_FALSE:

                retval = BodyNode(BRFalse(), index)
                self._items.append(retval)

                nopval = BodyNode(Nop(), index)
                self._items.append(nopval)



        elif type(item) is BinOp:

            # load left
            self._expand_item(item.left, index, store=False)
#            # load right
            self._expand_item(item.right, index, store=False)

            opval = BodyNode(item.op, index)
            self._items.append(opval)


        elif type(item) is Compare:

            print("LOADING COMPARE!!!!!")
            #load the left operand
            self._expand_item(item.left, index, store=False)

            #load the right operand
            right = item.comparators[0]
            self._expand_item(right, index, store=False)

            #create a new assignment value for the value of the operand

            opval = BodyNode(item.ops[0], index)
            self._items.append(opval)

        elif type(item) in [If, IfExp]:

            print("Parsing if: %s %s " % (item, vars(item)))

            #add the test clause firt
            self._build_item(item.test, index)


            #add the indicator for break false first
            #if it is not there, we need to add it
            brfalse = None

            for orelse in item.orelse:
                if type(orelse) is Return:
                    orelse.br_type = BR_FALSE
                    brfalse = orelse
            if brfalse is None:
                brfalse = Return()
                brfalse.br_type = BR_FALSE
                #item.orelse.append(Nop())

            self._build_item(brfalse, index)

            #now add the body items?
            #now add the non return body clauses
            for ifitem in item.body:
                if type(ifitem) is not Return:
                    self._build_item(ifitem, index)



            #now add the indicator for break true
            #if it is not there, we need to add it
            brtrue = None
            for ifitem in item.body:
                if type(item) is Return:
                    item.br_type = BR_TRUE
                    brtrue = item
            if brtrue is None:
                self._items.append(BodyNode(Nop(), index))
                brtrue = Return()
                brtrue.br_type = BR_TRUE

            self._build_item(brtrue, index)


            #and add the non return else clauses
            for orelse in item.orelse:
                if type(orelse) is not Return:
                    self._build_item(orelse, index)

        else:
            print("ITEM::: %s %s" % (item, type(item)))
            node = BodyNode(item, index)
            self._items.append(node)


