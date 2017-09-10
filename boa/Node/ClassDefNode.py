from boa.Node.ASTNode import ASTNode

from _ast import ClassDef

class ClassDefNode(ASTNode):


    def __init__(self, node):


        self._type = ClassDef

        super(ClassDefNode, self).__init__(node)





