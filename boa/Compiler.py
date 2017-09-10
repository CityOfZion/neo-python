
import ast

from _ast import Import,ImportFrom,ClassDef

import json

from boa.Node.ASTNode import ASTNode

class Compiler():

    __instance = None

    _nodes = None

    def __init__(self):
        self._nodes = []

    def Validate(self):

        for node in self._nodes:
            if not node.Validate():
                return False

        return True


    @property
    def Nodes(self):
        return self._nodes

    @staticmethod
    def Instance():
        if not Compiler.__instance:
            Compiler.__instance = Compiler()
        return Compiler.__instance




    @staticmethod
    def Compile(path):

        Compiler.__instance = None

        compiler = Compiler.Instance()
        file = open(path)
        data = file.read()
        file.close()
        node = None

        try:

            node = ast.parse(data)

        except Exception as e:
            print("Could not compile file %s :: %s " % (path, e))
            return False

        body = node.body

        for item in body:

            compiler._nodes.append( ASTNode.FromNode(item))

        result = False

        try:
            result = compiler.Validate()
        except Exception as e:
            print("could not validate file %s " % path)

        if result == True:
            print("Compiler %s "% compiler.ToJson())
            return compiler

        return None

    def ToJson(self):
        jsn = {}
        jsn['nodes'] = [str(i) for i in self._nodes]
        return json.dumps(jsn, indent=4)

