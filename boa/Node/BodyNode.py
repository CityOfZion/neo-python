from boa.Node.ASTNode import ASTNode
from neo.VM import OpCode

class BodyNode(ASTNode):

    _name = None

    _value = None

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value


    @property
    def bytes(self):
        return self._bytes


    @property
    def type(self):
        return type(self._node)

    @property
    def op(self):
        return self._code


    addr = None

    func_addr = None

    _bytes = None

    _src_addr = None

    _src_addr_switch = None

    _src_func = None

    _code = None

    def __init__(self, node, index):

        self._type = 'Body'

        self.addr = index
        self.func_addr = index

        self._src_addr_switch = []

        self._code = OpCode.NOP

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