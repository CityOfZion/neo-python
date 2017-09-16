
import ast

from _ast import ClassDef

import json

from boa.Node.ASTNode import ASTNode

from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryWriter import BinaryWriter
import binascii
import symtable
import pprint
import os


class Compiler():

    __instance = None

    data = None

    def build(self):

        pass

    @staticmethod
    def instance():

        if not Compiler.__instance:
            Compiler.__instance = Compiler()
        return Compiler.__instance

    @staticmethod
    def write_file(data, path):

        f = open(path, 'wb+')
        f.write(data)
        f.close()

    def save(self):
        pass

    @staticmethod
    def load_and_save(path, output_path=None):

        compiler = Compiler.load(path)
        compiler.Convert()
        out = compiler.save()

        fullpath = os.path.realpath(path)

        path, filename = os.path.split(fullpath)
        newfilename = filename.replace('.py', '.avm')
        outpath = "%s/%s" % (path, newfilename)

        if output_path is None:
            Compiler.write_file(out, outpath)
        else:
            Compiler.write_file(out, output_path)

        return out

    @staticmethod
    def load(path):

        Compiler.__instance = None

        compiler = Compiler.instance()

        file = open(path)
        compiler.data = file.read()
        file.close()
