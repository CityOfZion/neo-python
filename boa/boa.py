import os
import binascii
from boa.code.module import Module

from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryWriter import BinaryWriter

class Compiler():

    __instance = None

    modules = None

    def __init__(self):
        self.modules = []

    @staticmethod
    def instance():

        if not Compiler.__instance:
            Compiler.__instance = Compiler()
        return Compiler.__instance

    @property
    def default(self):
        try:
            return self.modules[0]
        except Exception as e:
            pass
        return None

    @staticmethod
    def write_file(data, path):

        f = open(path, 'wb+')
        f.write(data)
        f.close()

    def write(self):
        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)

        method = self.default.main
        writer.WriteBytes( method.write())

        out = stream.getbuffer()
        return bytes(out)

    @staticmethod
    def load_and_save(path, output_path=None):

        compiler = Compiler.load(path)

        data = compiler.write()

        fullpath = os.path.realpath(path)

        path, filename = os.path.split(fullpath)
        newfilename = filename.replace('.py', '.avm')
        outpath = '%s/%s' % (path, newfilename)

        if output_path is None:
            Compiler.write_file(data, outpath)
        else:
            Compiler.write_file(data, output_path)

        return data

    @staticmethod
    def load(path):

        Compiler.__instance = None

        compiler = Compiler.instance()

        module = Module(path)
        compiler.modules.append(module)

        return compiler
