from boa.Node.ASTNode import ASTNode
from boa.Node.BodyNode import BodyNode
from boa.Token.NeoToken import NeoToken,TokenConverter
from boa.Compiler import Compiler
from neo.VM import OpCode

from _ast import FunctionDef,Return,Assign,AugAssign

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
    def body(self):
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
        for item in self.Node.body:

            if type(item) in [Assign,AugAssign]:

                right = BodyNode(item.value, index)
                index += 1
                self._items.append(right)

                left = BodyNode(item.targets[0], index)
                index += 1
                self._items.append(left)

            else:
                node = BodyNode(item, index)
                self._items.append(node)
                index += 1

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

        print("types %s %s " % (self._argument_types, self._return_type))

        Compiler.Instance().RegisterMethod(self)



    def Convert(self):


        print("CONVERTING!!!!!! %s " % self)
        compiler = Compiler.Instance()
        compiler.TokenAddr = 0
        compiler.AddrConv = {}

        self._insert_begin()

        skipcount = 0

        has_returned=False

        for item in self._items:

            print("GOING THROUGH ITEMS %s " % item)
            if skipcount > 0:
                skipcount -=1

            else:

                if item.type == Return:
                    print("item is return!")
                    has_returned = True
                    self._insert_end(item)

                skipcount = TokenConverter._ConvertCode(item, self)


        if not has_returned and self.IsEntry:
            self._insert_end()

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

        for key, c in self._bodytokens:

            if c.needfix and c.code != OpCode.CALL:

                addr = compiler.AddrConv[c.srcaddr]
                addr_off = addr - c.addr
                c.byts = addr_off.to_bytes(2,'little')
                c.needfix = False

    def _insert_end(self, src=None):

        if src:
            TokenConverter._Convert1by1( OpCode.NOP, src, self)

        TokenConverter._Insert1(OpCode.FROMALTSTACK, "endcode", self)
        TokenConverter._Insert1(OpCode.DROP, "", self)

        if not src:
            TokenConverter._Insert1(OpCode.RET, "nil return", self)

    def Validate(self):

        return super(FunctionNode, self).Validate()



    def __str__(self):

        return "[Function Node] %s " % self._name