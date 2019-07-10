from neo.VM import OpCode
from typing import TYPE_CHECKING
from functools import lru_cache
import binascii

if TYPE_CHECKING:
    from neo.VM.Script import Script

_OperandSizeTable = {}
start = int.from_bytes(OpCode.PUSHBYTES1, 'little')
end = int.from_bytes(OpCode.PUSHBYTES75, 'little') + 1
for op_num in range(start, end):
    _OperandSizeTable[int.to_bytes(op_num, 1, 'little')] = op_num
_OperandSizeTable[OpCode.JMP] = 2
_OperandSizeTable[OpCode.JMPIF] = 2
_OperandSizeTable[OpCode.JMPIFNOT] = 2
_OperandSizeTable[OpCode.CALL] = 2
_OperandSizeTable[OpCode.APPCALL] = 20
_OperandSizeTable[OpCode.TAILCALL] = 20
_OperandSizeTable[OpCode.CALL_I] = 4
_OperandSizeTable[OpCode.CALL_E] = 22
_OperandSizeTable[OpCode.CALL_ED] = 2
_OperandSizeTable[OpCode.CALL_ET] = 22
_OperandSizeTable[OpCode.CALL_EDT] = 2


class Instruction:

    @classmethod
    def RET(cls):
        return cls(0x66)

    def __init__(self, opcode: int):
        self.OpCode = int.to_bytes(opcode, 1, 'little')
        self.Operand = bytearray()
        self._OperandSizeTable = _OperandSizeTable
        self._OperandSizePrefixTable = {}

    @property
    @lru_cache()
    def OperandSizePrefixTable(self):

        self._OperandSizePrefixTable[OpCode.PUSHDATA1] = 1
        self._OperandSizePrefixTable[OpCode.PUSHDATA2] = 2
        self._OperandSizePrefixTable[OpCode.PUSHDATA4] = 4
        self._OperandSizePrefixTable[OpCode.SYSCALL] = 1
        return self._OperandSizePrefixTable

    @property
    @lru_cache()
    def OperandSizeTable(self):
        return self._OperandSizeTable

    @classmethod
    def FromScriptAndIP(clss, script: 'Script', ip: int):
        ins = clss(script[ip])
        ip += 1
        operand_size = ins.OperandSizePrefixTable.get(ins.OpCode, 0)

        if operand_size == 0:
            operand_size = ins.OperandSizeTable.get(ins.OpCode, 0)
        elif operand_size == 1:
            ip, operand_size = ins.ReadByte(script, ip)
        elif operand_size == 2:
            ip, operand_size = ins.ReadUint16(script, ip)
        elif operand_size == 4:
            ip, operand_size = ins.ReadInt32(script, ip)

        if (operand_size > 0):
            ins.Operand = ins.ReadExactBytes(script, ip, operand_size)
        return ins

    @property
    def InstructionName(self):
        return OpCode.ToName(self.OpCode)

    @property
    def Size(self):
        prefixSize = self.OperandSizePrefixTable.get(self.OpCode, 0)

        if prefixSize > 0:
            return 1 + prefixSize + len(self.Operand)
        else:
            return 1 + self.OperandSizeTable.get(self.OpCode, 0)

    @property
    def TokenI16(self):
        return int.from_bytes(self.Operand, 'little', signed=True)

    @property
    def TokenI16_1(self):
        return int.from_bytes(self.Operand[2:], 'little', signed=True)

    @property
    def TokenU32(self):
        return int.from_bytes(self.Operand, 'little', signed=False)

    @property
    def TokenString(self):
        return self.Operand.decode('ascii')

    def ReadByte(self, script, ip):
        next_byte_index = ip + 1
        if next_byte_index > script.Length:
            raise ValueError
        return next_byte_index, script[ip]

    def ReadUint16(self, script, ip):
        if ip + 2 > script.Length:
            raise ValueError
        return ip + 2, int.from_bytes(script[ip:ip + 2], 'little', signed=False)

    def ReadInt32(self, script, ip):
        if ip + 4 > script.Length:
            raise ValueError
        return ip + 4, int.from_bytes(script[ip:ip + 4], 'little', signed=True)

    def ReadBytes(self, offset, count):
        if offset + count > len(self.Operand):
            raise Exception
        return self.Operand[offset:offset + count]

    def ReadExactBytes(self, script, ip, count):
        if ip + count > script.Length:
            raise ValueError
        return script[ip:ip + count]

    def __str__(self):
        return self.InstructionName
