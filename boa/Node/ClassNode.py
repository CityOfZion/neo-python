from boa.Node.ASTNode import ASTNode
from boa.Node.FunctionNode import FunctionNode


from _ast import ClassDef,FunctionDef

import importlib

class ClassNode(ASTNode):

    _name = None

    _basename = None

    _methods = None

    _body =  None




    @property
    def name(self):
        return self._name

    def __init__(self, node):


        self._type = ClassDef

        super(ClassNode, self).__init__(node)


    def _build(self):

        super(ClassNode, self)._build()


        self._name = self._node.name

        self._methods = []
        self._assignments = []

        for item in self._node.body:

            node = ASTNode.FromNode(item)

            if type(node) is FunctionNode:
                node._classref = self
                self._methods.append( node )
            else:
                self._assignments.append(node)


    def Validate(self):
        super(ClassNode, self).Validate()

        bases = self._node.bases

        if len(bases) == 0:
            raise Exception(
                "Smart Contract must have base class of neo.SmartContract.Framework.FunctionCode or neo.SmartContract.Framework.SmartContract")

        if len(bases) > 1:
            raise Exception("Smart Contract cannot have more than one base class")

        self._basename = bases[0].id

        try:
            module = importlib.import_module(self.SC_FRAMEWORK)
            cls = getattr(module, self._basename)
        except Exception as e:
            print("Could not import item %s.%s %s" % (self.SC_FRAMEWORK, self._basename, e))
            return False


        for method in self._methods:

            if not method.Validate():
                return False

        for assign in self._assignments:
            if not assign.Validate():
                return False

        return True


    def __str__(self):
        return "Class Definition: %s %s" % self._name