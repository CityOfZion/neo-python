from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.OpCode import *
from neo.VM import VMState
from neo.Cryptography.Crypto import Crypto
from neo.Fixed8 import Fixed8
import sys,os
from autologging import logged

@logged
class ApplicationEngine(ExecutionEngine):


    ratio = 100000
    gas_free = 10 * 100000000
    gas_amount = 0
    gas_consumed = 0
    testMode = False

    Trigger = None

    def GasConsumed(self):
        return Fixed8(self.gas_consumed)

    def __init__(self, trigger_type, container, table, service, gas, testMode=False):

        super(ApplicationEngine, self).__init__(container=container,crypto=Crypto.Default(), table=table, service=service)

        self.Trigger = trigger_type
        self.gas_amount = self.gas_free + gas.value
        self.testMode = testMode


    def CheckArraySize(self):

        maxArraySize = 1024

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            return True

        opcode = self.CurrentContext.NextInstruction

        if opcode == PACK or opcode == NEWARRAY:

            size = self.EvaluationStack.Peek().GetBigInteger()

            if size > maxArraySize:
                return False

            return True

        return True


    def CheckInvocationStack(self):

        maxStackSize = 1024

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            return True

        opcode = self.CurrentContext.NextInstruction

        if opcode == CALL or opcode == APPCALL:
            if self.InvocationStack.Count >= maxStackSize:
                return False

            return True

        return True

    def CheckItemSize(self):

        maxItemSize = 1024 * 1024

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            return True

        opcode = self.CurrentContext.NextInstruction

        if opcode == PUSHDATA4:

            if self.CurrentContext.InstructionPointer + 4 >= len(self.CurrentContext.Script):
                return False

            #TODO this should be double checked.  it has been
            #double checked and seems to work, but could possibly not work
            position = self.CurrentContext.InstructionPointer + 1
            lengthpointer = self.CurrentContext.Script[position:position+4]
            length = int.from_bytes(lengthpointer, 'little')

            if length > maxItemSize:
                return False

            return True


        elif opcode == CAT:

            if self.EvaluationStack.Count < 2:
                return False

            length=0

            try:
                length = len(self.EvaluationStack.Peek(0).GetByteArray()) + len(self.EvaluationStack.Peek(1).GetByteArray())
            except Exception as e:
                self.__log.debug("colud not get length %s " % e)

            if length > maxItemSize:
                return False

            return True

        return True


    def CheckStackSize(self):

        maxStackSize = 2 * 1024

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            return True

        size = 0

        opcode = self.CurrentContext.NextInstruction

        if opcode < PUSH16:
            size = 1

        else:

            if opcode in [DEPTH, DUP, OVER, TUCK]:
                size = 1

            elif opcode == UNPACK:

                item = self.EvaluationStack.Peek()

                if not item.IsArray:
                    return False

                size = len( item.GetArray())

        if size == 0:
            return True

        size += self.EvaluationStack.Count + self.AltStack.Count

        if size > maxStackSize:
            print("SIZE IS OVER MAX STACK SIZE!!!!")
            return False

        return True


    def Execute(self):

        while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0:

            try:

                self.gas_consumed = self.gas_consumed + self.GetPrice() * self.ratio

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.__log.debug(exc_type, fname, exc_tb.tb_lineno)
                self.__log.debug("exception calculating gas consumed %s " % e)
                print("Exception calculating gas consumed %s " % e)
                return False

            if not self.testMode and self.gas_consumed > self.gas_amount:
                return False

            if not self.CheckItemSize():
                return False

            if not self.CheckStackSize():
                return False

            if not self.CheckArraySize():
                return False

            if not self.CheckInvocationStack():
                return False

            self.StepInto()

        return not self._VMState & VMState.FAULT > 0


    def GetPrice(self):

        if self.CurrentContext.InstructionPointer >= len( self.CurrentContext.Script):
            return 0

        opcode = self.CurrentContext.NextInstruction

        if opcode <= PUSH16:
            return 0

        if opcode == NOP:
            return 0
        elif opcode == APPCALL or opcode == TAILCALL:
            return 10
        elif opcode == SYSCALL:
            return self.GetPriceForSysCall()
        elif opcode == SHA1 or opcode == SHA256:
            return 10
        elif opcode == HASH160 or opcode == HASH256:
            return 20
        elif opcode == CHECKSIG:
            return 100
        elif opcode == CHECKMULTISIG:
            if self.EvaluationStack.Count == 0:
                return 1
            n = self.EvaluationStack.Peek().GetBigInteger()

            if n < 1:
                return 1

            return 100 * n

        return 1


    def GetPriceForSysCall(self):

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script) - 3:
            return 1

        length = self.CurrentContext.Script[self.CurrentContext.InstructionPointer + 1]

        if self.CurrentContext.InstructionPointer > len(self.CurrentContext.Script) - length - 2:
            return 1

        strbytes = self.CurrentContext.Script[self.CurrentContext.InstructionPointer+2:length + self.CurrentContext.InstructionPointer + 2]

        api_name = strbytes.decode('utf-8')

        api = api_name.replace('Antshares.','Neo.')

        if api == "Neo.Runtime.CheckWitness":
            return 200

        elif api == "Neo.Blockchain.GetHeader":
            return 100

        elif api == "Neo.Blockchain.GetBlock":
            return 200

        elif api == "Neo.Blockchain.GetTransaction":
            return 100

        elif api == "Neo.Blockchain.GetAccount":
            return 100

        elif api == "Neo.Blockchain..GetValidators":
            return 200

        elif api == "Neo.Blockchain.GetAsset":
            return 100

        elif api == "Neo.Blockchain.GetContract":
            return 100

        elif api == "Neo.Blockchain.GetReferences":
            return 200

        elif api == "Neo.Account.SetVotes":
            return 1000

        elif api == "Neo.Validator.Register":
            return int(1000 * 100000000 / self.ratio)

        elif api == "Neo.Asset.Create":
            return int(5000 * 100000000 / self.ratio)

        elif api == "Neo.Asset.Renew":
            return int(self.EvaluationStack.Peek(1).GetBigInteger() * 5000 * 100000000 / self.ratio)

        elif api == "Neo.Contract.Create" or api == "Neo.Contract.Migrate":
            amount = int(500 * 100000000 / self.ratio)
            return amount

        elif api == "Neo.Storage.Get":
            return 100

        elif api == "Neo.Storage.Put":
            l1 = len(self.EvaluationStack.Peek(1).GetByteArray())
            l2 = len(self.EvaluationStack.Peek(2).GetByteArray())

            return int(((l1 + l2 - 1) / 1024 + 1) * 1000)

        elif api == "Neo.Storage.Delete":
            return 100


        return 1

