from neo.VM import OpCode

from boa.Compiler import Compiler
from neo.BigInteger import BigInteger

class NeoToken():


    code = OpCode.NOP
    addr = 0
    byts = None
    srcaddr = None
    srcaddr_switch = None
    src_func = None



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