from boa.Node.ASTNode import ASTNode
from boa.Node.BodyNode import BodyNode

from boa.Compiler import Compiler

from _ast import FunctionDef

class FunctionNode(ASTNode):

    _name = None

    _decorators = None

    _items = None


    _arguments = None


    _classref = None

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

        Compiler.Instance().RegisterMethod(self)



    def Validate(self):

        return super(FunctionNode, self).Validate()



    def __str__(self):

        return "[Function Node] %s " % self._name