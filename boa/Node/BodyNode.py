from boa.Node.ASTNode import ASTNode


class BodyNode(ASTNode):

    _name = None

    _value = None

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value



    def __init__(self, node):

        self._type = 'Body'

        super(BodyNode, self).__init__(node)


    def _build(self):
        super(BodyNode, self)._build()

#        target = self._node.targets[0]
#        self._name = target.id
#
#        self._value = self._node.n

        print("creattign body: %s " % self)

    def Validate(self):

        return super(BodyNode, self).Validate()



    def __str__(self):

        return "[Body Node] %s" % (self._node)