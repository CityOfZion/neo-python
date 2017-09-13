from boa.Node.ASTNode import ASTNode
from boa.Node.BodyNode import BodyNode
from boa.Token.NeoToken import NeoToken,TokenConverter,Nop
from boa.Compiler import Compiler
from neo.VM import OpCode
import pdb
from _ast import FunctionDef,Return,Assign,AugAssign,Load,Store,Name,Break



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


    @property
    def BodyTokens(self):
        return self._BodyTokens

    @BodyTokens.setter
    def BodyTokens(self, value):

        self._BodyTokens = value

    def InsertBodyToken(self, token, addr ):
        if self.BodyTokens is None:
            self.BodyTokens = {}

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



    def __init__(self, node):

        self._type = FunctionDef
        self._decorators = []
        self._items = []
        self._arguments = []

        self._bodytokens = {}

        super(FunctionNode, self).__init__(node)


    def _build(self):
        super(FunctionNode, self)._build()

        self._name = self._node.name

        if self._name=='Main':
            Compiler.Instance().RegisterEntry(self)

        self._decorators = [item.id for item in self._node.decorator_list]

        index=0

        nop = BodyNode(Nop(),0)
        self._items.append(nop)

        has_returned = False

        for item in self.Node.body:

            if type(item) in [Assign,AugAssign]:

                right = BodyNode(item.value, index)
                self._items.append(right)

                left = BodyNode(item.targets[0], index)
                self._items.append(left)

            elif type(item) is Return:
                has_returned = True
                #push the value of the item to be returned
                val = item.value
                pushval = BodyNode(val, index)
                self._items.append(pushval)

                #now store the value of the item to be returned
                val = Name()
                val.ctx = Store()
                storeval = BodyNode(val, index)
                self._items.append(storeval)

                #now we indicate an exit
                breakval = BodyNode(Break(), index)
                self._items.append(breakval)

                #and then load the value
                val = Name()
                val.ctx = Load()
                loadval = BodyNode(val, index)
                self._items.append(loadval)


                #we need a nop first befor return
                nopval = BodyNode(Nop(), index)
                self._items.append(nopval)

                retval = BodyNode(item, index)
                self._items.append(retval)

            else:
                node = BodyNode(item, index)
                self._items.append(node)

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

        self._arguments = [arg.arg for arg in self.Node.args.args]

        try:
            self._argument_types = [arg.annotation.id for arg in self.Node.args.args]
        except Exception as e:
            print("could not get types for method arguments %s " % e)
            pass

        try:
            self._return_type = self.Node.returns.id
        except Exception as e:
#            print("could not load return type %s " % e)
            self._return_type = None

#        print("types %s %s " % (self._argument_types, self._return_type))

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

        varcount = len(self._arguments) + len(self._node.body)
        TokenConverter._InsertPushInteger(varcount, "begincode", self)
        TokenConverter._Insert1(OpCode.NEWARRAY, "", self)
        TokenConverter._Insert1(OpCode.TOALTSTACK, "", self)


        for i in range(0, len(self._arguments)):

            TokenConverter._Insert1(OpCode.FROMALTSTACK, "set param %s" % i, self)
            TokenConverter._Insert1(OpCode.DUP, "", self)
            TokenConverter._Insert1(OpCode.TOALTSTACK, "", self)

            TokenConverter._InsertPushInteger(i, "", self)
            TokenConverter._InsertPushInteger(2, "", self)
            TokenConverter._Insert1(OpCode.ROLL, "", self)
            TokenConverter._Insert1(OpCode.SETITEM, "", self)


    def _convert_addr_in_method(self):

        compiler = Compiler.Instance()
        print("CONVERTING ADDR IN METHOD!!!!")
        for key, c in self._BodyTokens.items():
            print("converting addr in method!!! %s %s %s" % (c, c.code, c.needfix))
            if c.needfix and c.code != OpCode.CALL:
                pprint.pprint(compiler.AddrConv)
                print("code src adrd %s " % c.srcaddr)
                print("c addr %s " % c.addr)
#                print("c func addr %s " % c.fun)
                addr = compiler.AddrConv[c.offset + 1]
                print("ADDR COMP %s " % addr)
                pprint.pprint(c)
                print("c vars %s " % vars(c))
                addr_off = addr - c.addr
                print("addr offset %s " % addr_off)
#                pdb.set_trace()
                c.byts = addr_off.to_bytes(2,'little')
                print("c bytes %s " % c.byts)
                c.needfix = False

    def _insert_end(self, src=None):

        TokenConverter._Insert1(OpCode.FROMALTSTACK, "endcode", self)
        TokenConverter._Insert1(OpCode.DROP, "", self)


    def Validate(self):

        return super(FunctionNode, self).Validate()



    def __str__(self):

        return "[Function Node] %s " % self._name