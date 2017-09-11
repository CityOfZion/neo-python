from boa.Node.ASTNode import ASTNode
from boa.Node.BodyNode import BodyNode
from boa.Token.NeoToken import NeoToken,TokenConverter
from boa.Compiler import Compiler
from neo.VM import OpCode

from _ast import FunctionDef

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


        for item in self.Node.body:
            node = ASTNode.FromNode(item)
            self._items.append(node)

        self._arguments = [arg.arg for arg in self.Node.args.args]

        try:
            self._argument_types = [arg.annotation.id for arg in self.Node.args.args]
        except Exception as e:
            print("could not get types for method arguments %s " % e)
            pass

        try:
            self._return_type = self.Node.returns.id
        except Exception as e:
            print("could not load return type")
            pass

        print("types %s %s " % (self._argument_types, self._return_type))

        Compiler.Instance().RegisterMethod(self)



    def Convert(self):

        compiler = Compiler.Instance()
        compiler.TokenAddr = 0
        compiler.AddrConv = []

        self._insert_begin()



        self._insert_end()

    def _insert_begin(self):

        varcount = len(self._arguments) + len(self._items)
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

    def _insert_end(self):

        # @TODO _Convert1by1( OpCode.NOP, src, to)

        TokenConverter._Insert1(OpCode.FROMALTSTACK, "endcode", self)
        TokenConverter._Insert1(OpCode.DROP, "", self)

        pass


    def Validate(self):

        return super(FunctionNode, self).Validate()



    def __str__(self):

        return "[Function Node] %s " % self._name