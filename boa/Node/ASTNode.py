
from _ast import ImportFrom,Import,ClassDef


class ASTNode():

    _node = None

    _children = None

    _type = None


    _line = 0


    def __init__(self, node):

        self._node = node

        self._children = []

        self._build()

    def _build(self):

        self._line = self._node.lineno


    @property
    def Type(self):
        return self._type

    @property
    def Node(self):
        return self._node

    @property
    def Line(self):
        return self._line



    def Validate(self):
        return True


    def ToJson(self):
        pass

    def __str__(self):
        return '[%s] AST Node %s ' % (self._type, self._node)



    @staticmethod
    def FromNode(node):

        from boa.Node.ClassDefNode import ClassDefNode
        from boa.Node.ImportNode import ImportNode,ImportFromNode

        typ = type(node)

        if typ is ClassDef:
            return ClassDefNode(node)

        elif typ is ImportFrom:
            return ImportFromNode(node)
        elif typ is Import:
            return ImportNode(node)

        return ASTNode(node)

#            raise Exception("Node type %s not implemented %s " % typ)
