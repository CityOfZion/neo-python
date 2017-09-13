from boa.Node.ASTNode import ASTNode
from neo.VM import OpCode
from ast import Assign

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
        if self._node:
            return type(self._node)
        return self._code

    @property
    def op(self):
        return self._code


    addr = None
    offset = None

    _bytes = None


    _code = None


    def __init__(self, node, index, offset=None, op=None):

        self._type = 'Body'

        self.addr = index
        self.offset = offset

        self._meta = False

        if op is None:
            self._code = OpCode.NOP
        else:
            self._code = op

        super(BodyNode, self).__init__(node)


    def _build(self):
        super(BodyNode, self)._build()


        if type(self._node) is Assign:
            print("vars %s " % self._node)

            target = self._node.targets[0]

            if target.id == 'expected':
                self._meta = True
                self._name = 'expected'
                self._value = self._node.value.s

#        target = self._node.targets[0]
#        self._name = target.id
#
#        self._value = self._node.n


    def Validate(self):

        return super(BodyNode, self).Validate()


    def AddrOffset(self):
        return "Body Node: Addr: %s Offset %s " % (self.addr, self.offset)

    def __str__(self):
        if self._node:
            return "[Body Node] %s" % (self._node)
        return "[Body Node] %s " % self._code