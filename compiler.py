
import ast

from _ast import Import,ImportFrom,ClassDef

import json


class Compiler():

    __instance = None

    imports = None
    classdefs = None

    def __init__(self):
        self.imports = []
        self.classdefs = []


    def validate(self):
        if not self._validate_imports(): return False
        if not self._validate_classes(): return False

        return True

    def _validate_imports(self):
        return True

    def _validate_classes(self):
        return True

    @staticmethod
    def Instance():
        if not Compiler.__instance:
            Compiler.__instance = Compiler()
        return Compiler.__instance




    @staticmethod
    def Compile(path):

        compiler = Compiler.Instance()
        file = open(path).read()

        node = None

        try:

            node = ast.parse(file)

        except Exception as e:
            print("Could not compile file %s :: %s " % (path, e))
            return False

        body = node.body

        for item in body:

            if type(item) is ImportFrom:
                compiler.imports.append(item)

            elif type(item) is ClassDef:
                compiler.classdefs.append(item)


        compiler.validate()

        print("Compiler %s "% compiler.ToJson())
        return True

    def ToJson(self):
        jsn = {}
        jsn['imports'] = [str(i) for i in self.imports]
        jsn['classes'] = [str(i) for i in self.classdefs]
        return json.dumps(jsn, indent=4)



Compiler.Compile('./boa/sources/Math.py')

#dump = ast.dump(node,annotate_fields=True, include_attributes=True)


#print

#print("Dump %s " % dump)




