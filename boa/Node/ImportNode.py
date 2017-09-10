from boa.Node.ASTNode import ASTNode

from _ast import ImportFrom

import sys

import importlib

class ImportNode(ASTNode):

    _names = None

    def __init__(self, node):
        super(ImportNode, self).__init__(node)
        self._names = []


    def _build(self):
        self._names = []
        for item in self._node.names:
            self._names.append(item.name)

        print("built import node, names: %s " % self._names)

    def Validate(self):

        raise Exception("Cannot import items %s " % self._names)




class ImportFromNode(ASTNode):

    SC_FRAMEWORK = 'neo.SmartContract.Framework'

    _module_name = None
    _classnames = None

    def __init__(self, node):


        self._type = ImportFrom
        self._classnames = []


        super(ImportFromNode, self).__init__(node)

    def _build(self):

        super(ImportFromNode, self)._build()

        self._module_name = self._node.module

        for item in self._node.names:
            self._classnames.append(item.name)



    def Validate(self):
        super(ImportFromNode, self).Validate()

        if not self.SC_FRAMEWORK in self._module_name:
            raise Exception("Importing is only allowed from %s module and submodules" % self.SC_FRAMEWORK)

        module = None
        try:
            module = importlib.import_module(self._module_name)
        except Exception as e:
            print("Could not import module %s %s" % (self._module_name, e))


        for classname in self._classnames:
            try:
                cls = getattr(module,classname)
            except Exception as e:
                print("Could not import item %s.%s " % (self._module_name, classname) )
                return False

        return True

    @property
    def ImportedClasses(self):
        return ['%s.%s' % (self._module_name, name) for name in self._classnames]



