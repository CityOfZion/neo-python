
import ast

from _ast import Import,ImportFrom,ClassDef

import json

from boa.Node.ASTNode import ASTNode

from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryWriter import BinaryWriter
import binascii

class Compiler():

    __instance = None

    _nodes = None

    _entry_method = None

    _all_methods = None

    _TokenAddr = 0
    _AddrConv = None



    def __init__(self):
        self._nodes = []
        self._entry_method = None
        self._all_methods = []
        self._AddrConv = {}

    def Validate(self):

        for node in self._nodes:
            if not node.Validate():
                return False

        return True


    @property
    def TokenAddr(self) -> int:
        return self._TokenAddr

    @TokenAddr.setter
    def TokenAddr(self, value: int):
        self._TokenAddr = value

    @property
    def AddrConv(self):
        return self._AddrConv

    @AddrConv.setter
    def AddrConv(self, value):
        self._AddrConv = value

    @property
    def Nodes(self):
        return self._nodes

    @property
    def Entry(self):
        return self._entry_method

    @property
    def Methods(self):
        return self._all_methods

    def RegisterEntry(self, function_def):
        self._entry_method = function_def

    def RegisterMethod(self, function_def):
        if not function_def in self._all_methods:
            self._all_methods.append(function_def)

    def Convert(self):
        print("Converting...")

        for node in self._nodes:

            if node.Type is ClassDef:

                node.Convert()

    def Save(self):
        print("saving...")

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream=stream)

        self.WriteFunc(writer, self.Entry)

        for method in self._all_methods:
            if not method.IsEntry:
                self.WriteFunc(writer,method)

        out = stream.ToArray()
        outb = binascii.unhexlify(out)
#        print("OUT %s  " % out)
        print("OUT B: %s " % outb)

        StreamManager.ReleaseStream(stream)

        return outb

    def WriteFunc(self, writer, func):
#        print("writing function body items %s " % func.BodyTokens)

        tokens = func.BodyTokens
        for key in sorted(tokens.keys()):
            val = tokens[key]
#            print("writing key %s -> %s" % (key, val.code))

            writer.WriteByte(val.code)



    @staticmethod
    def Instance():
        if not Compiler.__instance:
            Compiler.__instance = Compiler()
        return Compiler.__instance


    @staticmethod
    def LoadAndSave(path, output_path=None):
        compiler = Compiler.Load(path)
        compiler.Convert()
        out = compiler.Save()
        return out


    @staticmethod
    def Load(path):

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
            print("could not validate file %s %s" % (path, e))

        if result == True:
#            print("Compiler %s "% compiler.ToJson())
            return compiler

        return None

    def ToJson(self):
        jsn = {}
        jsn['nodes'] = [str(i) for i in self._nodes]
        return json.dumps(jsn, indent=4)

