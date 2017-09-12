from neo.VM import OpCode

from boa.Compiler import Compiler
from neo.BigInteger import BigInteger

from _ast import Return,Load,Set,Assign,AugAssign,If,IfExp,Name,Num,Store,Del

import pprint

class NeoToken():


    code = OpCode.NOP
    addr = 0
    byts = None
    srcaddr = None
    srcaddr_switch = None
    src_func = None

    tokenAddr_Index = None
    tokenAddr_Switch = None

    token_field = None
    tokenType = None
    tokenMethod = None
    tokenI32 = None
    tokenI64 = None

    tokenR32 = None
    tokenR64 = None

    tokenStr = None

    def __init__(self):
        self.tokenAddr_Switch = []


    def __str__(self):
        return "[Neo Token %s -> %s]" % (self.code, self.addr)

class TokenConverter():


    @staticmethod
    def _Insert1(code, comment:str, to, data: bytearray = None) -> NeoToken:


        token = NeoToken()

        startaddr = Compiler.Instance().TokenAddr

        token.addr = startaddr


        Compiler.Instance().TokenAddr += 1

        token.code = code

        if data is not None:
            token.byts = data

            dlen = len(data)

            Compiler.Instance().TokenAddr += dlen

        to.InsertBodyToken(token, startaddr)

        return token


    @staticmethod
    def _InsertPushData(data: bytearray, comment:str, to) -> NeoToken:

        dlen = len(data)
        if dlen == 0:
            return TokenConverter._Insert1(OpCode.PUSH0, comment,to)
        elif dlen <= 75:
            return TokenConverter._Insert1(dlen, comment, to, data)

        prefixlen = 0
        code=None

        if dlen < 0x100:
            prefixlen = 1
            code = OpCode.PUSHDATA1
        elif dlen < 0x1000:
            prefixlen = 2
            code = OpCode.PUSHDATA2
        else:
            prefixlen = 4
            code = OpCode.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return TokenConverter._Insert1(code, comment, to, byts)


    @staticmethod
    def _InsertPushInteger(i: int, comment: str, to) -> NeoToken:
        if i == 0:
            return TokenConverter._Insert1(OpCode.PUSH0, comment, to)
        elif i == -1:
            return TokenConverter._Insert1(OpCode.PUSHM1, comment, to)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            print("PUSHING INTEGER %s " % out)
            return TokenConverter._Insert1(out, comment, to)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return TokenConverter._InsertPushData(outdata, comment, to)




    @staticmethod
    def _Convert1by1(op, src, method, data=None):

        print("Convert 1 by 1: %s %s %s" % (op, src, method))

        compiler = Compiler.Instance()

        token = NeoToken()
        start_addr = compiler.TokenAddr

        token.addr = start_addr

        if src is not None:
            print("Source %s %s" % (src, src.addr))
            compiler.AddrConv[src.addr] = start_addr


        compiler.TokenAddr += 1

        token.code = op

        if data is not None:

            token.byts = data
            compiler.TokenAddr += len(data)

        method.BodyTokens[start_addr] = token

        return token


    @staticmethod
    def _ConvertPushData(data, src, to):

        dlen = len(data)
        if dlen == 0:
            return TokenConverter._Convert1by1(OpCode.PUSH0, src, to)
        elif dlen <= 75:
            return TokenConverter._Convert1by1(len(data), src, to, data)

        prefixlen = 0
        code = None

        if dlen < 0x100:
            prefixlen = 1
            code = OpCode.PUSHDATA1
        elif dlen < 0x1000:
            prefixlen = 2
            code = OpCode.PUSHDATA2
        else:
            prefixlen = 4
            code = OpCode.PUSHDATA4

        byts = bytearray(dlen.to_bytes(prefixlen, 'little')) + data

        return TokenConverter._Convert1by1(code, src, to, byts)

    @staticmethod
    def _ConvertPushInteger(i, src, to):
        if i == 0:
            return TokenConverter._Convert1by1(OpCode.PUSH0, src, to)
        elif i == -1:
            return TokenConverter._Convert1by1(OpCode.PUSHM1, src, to)
        elif i > 0 and i <= 16:
            out = 0x50 + i
            print("OUT IS %s " % out)
            return TokenConverter._Convert1by1(out, src, to)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return TokenConverter._ConvertPushData(outdata, src, to)

    @staticmethod
    def _ConvertStLoc(src, to, pos):

        #set array
        TokenConverter._Convert1by1(OpCode.FROMALTSTACK, src, to)
        TokenConverter._Convert1by1(OpCode.DUP, None, to)
        TokenConverter._Convert1by1(OpCode.TOALTSTACK, None, to)

        #set i?
        TokenConverter._ConvertPushInteger(pos + len(to.arguments), None, to)

        #set item
        TokenConverter._ConvertPushInteger(2, None, to)
        TokenConverter._Convert1by1(OpCode.ROLL, None, to)
        TokenConverter._Convert1by1(OpCode.SETITEM, None, to)

    @staticmethod
    def _ConvertLdLoc(src, to, pos):

        # get array
        TokenConverter._Convert1by1(OpCode.FROMALTSTACK, src, to)
        TokenConverter._Convert1by1(OpCode.DUP, None, to)
        TokenConverter._Convert1by1(OpCode.TOALTSTACK, None, to)

        # get i?
        TokenConverter._ConvertPushInteger(pos + len(to.arguments), None, to)
        TokenConverter._Convert1by1(OpCode.PICKITEM, None, to)



    @staticmethod
    def _ConvertCode(src, to):

        skipcount = 0

        print("Converting code %s " % src)
        pprint.pprint(src)

        ctype = type(src._node)

        if ctype is Return:
            print("Converting return!!")
            TokenConverter._Convert1by1(OpCode.RET, src, to)

#        elif ctype is Assign:
#            print("assign %s " % src)

#        elif ctype is Load:
#            print("LOAD %s " % Load)


        elif ctype is Num:
            print("CONVERTING NUMMMMMM %s " % src._node)
            TokenConverter._ConvertPushInteger(src._node.n,src, to)
#        elif ctype is

        elif ctype is Name:
            print("ctype converting name!!!! %s" % (src._node.ctx))
            if type(src._node.ctx) is Store:
                print("Storing location.... %s %s %s " % ( src, to, src.func_addr))
                TokenConverter._ConvertStLoc(src, to, src.func_addr)
            elif type(src._node.ctx) is Load:
                TokenConverter._ConvertStLoc(src, to, src.func_addr)
            elif type(src._node.ctx) is Del:
                pass
            else:
                print("colud not convert name object....")


        elif ctype is If:
            print("Convert if!")
            token = TokenConverter._Convert1by1(OpCode.JMP, src, to, bytearray(2))
            token.nedfix = True
            token.srcaddr = src.tokenAddr
        else:
            print("other type: %s " % type(src))

        return skipcount