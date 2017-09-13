from neo.VM import OpCode

from boa.Compiler import Compiler
from neo.BigInteger import BigInteger

from _ast import Return,Load,Set,Assign,AugAssign,If,IfExp,Name,Num,Store,Del,Break,stmt

import pdb

import pprint

class Nop(stmt):
    pass

class NeoToken():


    code = OpCode.NOP
    addr = 0
    srcaddr=0
    offset = 0
    byts = None

    tokenAddr_Index = None
    tokenAddr_Switch = None

    needfix = False

    def __init__(self):
        self.tokenAddr_Switch = []
        self.needfix = False

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
            return TokenConverter._Insert1(out, comment, to)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return TokenConverter._InsertPushData(outdata, comment, to)




    @staticmethod
    def _Convert1by1(op, src, method, data=None):

        print("CONVERTING 1 by 1 %s %s " % (op, src))
        compiler = Compiler.Instance()

        token = NeoToken()
        start_addr = compiler.TokenAddr
        token.addr = start_addr

        if src is not None:
            token.offset = src.offset
            compiler.AddrConv[src.offset] = start_addr


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
            return TokenConverter._Convert1by1(out, src, to)

        bigint = BigInteger(i)
        outdata = bigint.ToByteArray()

        return TokenConverter._ConvertPushData(outdata, src, to)

    @staticmethod
    def _ConvertStLoc(src, to, pos):

        print("STORE ITEM %s %s " % (src, pos))

        if src._node.id is not None:
            if not src._node.id in to.StoreTable.keys():
                to.StoreTable[src._node.id] = pos
                print("ADDING ITEM/POS TO STORE %s %s " % (src._node.id, pos))

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
        print("LOAD ITEM %s %s " % (src, pos))

        position = pos + len(to.arguments)
        if src._node.id is not None:
            print("LOAD NODE id  from store table %s " % src._node.id)

            if src._node.id in to.StoreTable.keys():
                print("changing pos from %s " % position)
                position = to.StoreTable[src._node.id] + len(to.arguments)
                print("changed pos to %s " % position)

            elif src._node.id in to.arguments:
                position = to.arguments.index(src._node.id)

        # get array
        TokenConverter._Convert1by1(OpCode.FROMALTSTACK, src, to)
        TokenConverter._Convert1by1(OpCode.DUP, None, to)
        TokenConverter._Convert1by1(OpCode.TOALTSTACK, None, to)

        # get i?
        TokenConverter._ConvertPushInteger(position, None, to)
        TokenConverter._Convert1by1(OpCode.PICKITEM, None, to)



    @staticmethod
    def _ConvertCode(src, to):

        skipcount = 0

        pprint.pprint(src)

        if src._node:



            ctype = type(src._node)

            print("CONVERTING: :%s " % ctype)

            if ctype is Nop:
                print("")
                token = TokenConverter._Convert1by1(OpCode.NOP, src, to)

            elif ctype is Return:
                print("CONERTING RETURN!!!")
                token = TokenConverter._Convert1by1(OpCode.RET, src, to)
                print("converted return! %s " % token)

            elif ctype is Break:
                print("CONVERTING JUMP!!!!!!")
                token = TokenConverter._Convert1by1(OpCode.JMP, src, to, bytearray(2))
                token.needfix = True
                token.srcaddr = src.addr


            elif ctype is Num:
                print("CONVERTING NUM!!!!!!!!")
                TokenConverter._ConvertPushInteger(src._node.n,src, to)
    #        elif ctype is

            elif ctype is Name:
                if type(src._node.ctx) is Store:
                    TokenConverter._ConvertStLoc(src, to, src.addr)
                elif type(src._node.ctx) is Load:
                    TokenConverter._ConvertLdLoc(src, to, src.addr)
                elif type(src._node.ctx) is Del:
                    pass
                else:
                    print("colud not convert name object....")


            elif ctype is If:
                token = TokenConverter._Convert1by1(OpCode.JMP, src, to, bytearray(2))
                token.needfix = True
                token.srcaddr = src.tokenAddr
            else:
                print("other type: %s " % type(src))
                pdb.set_trace()


        return skipcount