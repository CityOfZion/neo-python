
from _ast import ImportFrom,Import,ClassDef,FunctionDef


class ASTNode():

    SC_FRAMEWORK = 'neo.SmartContract.Framework'

    _node = None

    _children = None

    _type = None



    _address = None


    @property
    def Type(self):
        return self._type

    @property
    def Node(self):
        return self._node

    @property
    def Line(self):
        return self._node.lineno

    @property
    def Address(self):
        return self._address


    @property
    def name(self):
        return 'AST Node'

    def __init__(self, node):

        self._node = node

        self._children = []

        self._build()

    def _build(self):
        pass


    def Convert(self):
        pass


    def Validate(self):
        return True


    def ToJson(self):
        pass

    def __str__(self):
        return '[%s] AST Node %s ' % (self._type, self._node)



    @staticmethod
    def FromNode(node):

        from boa.Node.ClassNode import ClassNode
        from boa.Node.ImportNode import ImportNode,ImportFromNode
        from boa.Node.FunctionNode import FunctionNode
        from boa.Node.BodyNode import BodyNode

        typ = type(node)

        if typ is ClassDef:
            return ClassNode(node)
        elif typ is ImportFrom:
            return ImportFromNode(node)
        elif typ is Import:
            return ImportNode(node)
        elif typ is FunctionDef:
            return FunctionNode(node)

#        print("Node type %s not explicitly supported  %s " % typ)

        return BodyNode(node)

#            raise Exception("Node type %s not implemented %s " % typ)
