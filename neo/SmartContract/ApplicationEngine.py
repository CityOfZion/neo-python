import binascii
import hashlib
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Fixed8 import Fixed8
from neo.Core.UInt160 import UInt160
from neo.Core.State.ContractState import ContractPropertyState

# used for ApplicationEngine.Run
from neo.SmartContract import TriggerType
from neo.VM import OpCode
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.InteropService import Array
from neo.VM.OpCode import APPCALL, TAILCALL, \
    SYSCALL, NOP, SHA256, SHA1, HASH160, HASH256, CHECKSIG, CHECKMULTISIG, VERIFY
from neo.logging import log_manager
from neo.SmartContract.StateMachine import StateMachine
from neo.EventHub import events

logger = log_manager.getLogger('vm')


def interop_hash(method):
    return int.from_bytes(hashlib.sha256(method.encode()).digest()[:4], 'little', signed=False)


HASH_NEO_ASSET_CREATE = interop_hash("Neo.Asset.Create")
HASH_ANT_ASSET_CREATE = interop_hash("AntShares.Asset.Create")
HASH_NEO_ASSET_RENEW = interop_hash("Neo.Asset.Renew")
HASH_ANT_ASSET_RENEW = interop_hash("AntShares.Asset.Renew")
HASH_NEO_CONTRACT_CREATE = interop_hash("Neo.Contract.Create")
HASH_NEO_CONTRACT_MIGRATE = interop_hash("Neo.Contract.Migrate")
HASH_ANT_CONTRACT_CREATE = interop_hash("AntShares.Contract.Create")
HASH_ANT_CONTRACT_MIGRATE = interop_hash("AntShares.Contract.Migrate")
HASH_SYSTEM_STORAGE_PUT = interop_hash("System.Storage.Put")
HASH_SYSTEM_STORAGE_PUTEX = interop_hash("System.Storage.PutEx")
HASH_NEO_STORAGE_PUT = interop_hash("Neo.Storage.Put")
HASH_ANT_STORAGE_PUT = interop_hash("AntShares.Storage.Put")


class ApplicationEngine(ExecutionEngine):
    ratio = 100000
    gas_free = 10 * 100000000
    max_free_ops = 500000

    def GasConsumed(self):
        return Fixed8(self.gas_consumed)

    def __init__(self, trigger_type, container, snapshot, gas, testMode=False, exit_on_error=True):

        super(ApplicationEngine, self).__init__(container=container, crypto=Crypto.Default(), table=snapshot, service=StateMachine(trigger_type, snapshot),
                                                exit_on_error=exit_on_error)

        self.gas_amount = self.gas_free + gas.value
        self.testMode = testMode
        self.snapshot = snapshot
        self._is_stackitem_count_strict = True
        self.debugger = None
        self.gas_consumed = 0
        self.invocation_args = None

    def CheckDynamicInvoke(self):
        cx = self.CurrentContext
        opcode = cx.CurrentInstruction.OpCode

        if opcode in [OpCode.APPCALL, OpCode.TAILCALL]:
            script_hash = cx.CurrentInstruction.Operand

            for b in script_hash:
                # if any of the bytes are greater than 0, this is a normal app call
                if b > 0:
                    return True

            # if this is a dynamic app call, we will arrive here
            # get the current executing script hash
            current = UInt160(data=cx.ScriptHash())
            current_contract_state = self.snapshot.Contracts[current.ToBytes()]

            # if current contract state cant do dynamic calls, return False
            return current_contract_state.HasDynamicInvoke
        elif opcode in [OpCode.CALL_ED, OpCode.CALL_EDT]:
            current = UInt160(data=cx.ScriptHash())
            current_contract_state = self.snapshot.Contracts[current.ToBytes()]
            return current_contract_state.HasDynamicInvoke

        else:
            return True

    def PreExecuteInstruction(self):
        if self.CurrentContext.InstructionPointer >= self.CurrentContext.Script.Length:
            return True
        self.gas_consumed = self.gas_consumed + (self.GetPrice() * self.ratio)
        if not self.testMode and self.gas_consumed > self.gas_amount:
            return False
        if self.testMode and self.ops_processed > self.max_free_ops:
            logger.debug("Too many free operations processed")
            return False
        try:
            if not self.CheckDynamicInvoke():
                return False
        except Exception:
            pass
        return True

    def GetPrice(self):

        opcode = self.CurrentContext.CurrentInstruction.OpCode
        if opcode <= NOP:
            return 0

        elif opcode in [APPCALL, TAILCALL]:
            return 10
        elif opcode == SYSCALL:
            return self.GetPriceForSysCall()
        elif opcode in [SHA1, SHA256]:
            return 10
        elif opcode in [HASH160, HASH256]:
            return 20
        elif opcode in [CHECKSIG, VERIFY]:
            return 100
        elif opcode == CHECKMULTISIG:
            if self.CurrentContext.EvaluationStack.Count == 0:
                return 1

            item = self.CurrentContext.EvaluationStack.Peek()
            if isinstance(item, Array):
                n = item.Count
            else:
                n = item.GetBigInteger()

            if n < 1:
                return 1

            return 100 * n

        else:
            return 1

    def GetPriceForSysCall(self):
        instruction = self.CurrentContext.CurrentInstruction
        api_hash = instruction.TokenU32 if len(instruction.Operand) == 4 else interop_hash(instruction.TokenString)

        price = self._Service.GetPrice(api_hash)

        if price > 0:
            return price

        if api_hash == HASH_NEO_ASSET_CREATE or api_hash == HASH_ANT_ASSET_CREATE:
            return int(5000 * 100000000 / self.ratio)

        if api_hash == HASH_ANT_ASSET_RENEW or api_hash == HASH_ANT_ASSET_RENEW:
            return int(self.CurrentContext.EvaluationStack.Peek(1).GetBigInteger() * 5000 * 100000000 / self.ratio)

        if api_hash == HASH_NEO_CONTRACT_CREATE or api_hash == HASH_NEO_CONTRACT_MIGRATE or api_hash == HASH_ANT_CONTRACT_CREATE or api_hash == HASH_ANT_CONTRACT_MIGRATE:
            fee = int(100 * 100000000 / self.ratio)  # 100 gas for contract with no storage no dynamic invoke

            contract_properties = self.CurrentContext.EvaluationStack.Peek(3).GetBigInteger()
            if contract_properties < 0 or contract_properties > 0xff:
                raise ValueError("Invalid contract properties")

            if contract_properties & ContractPropertyState.HasStorage > 0:
                fee += int(400 * 100000000 / self.ratio)  # if contract has storage, we add 400 gas

            if contract_properties & ContractPropertyState.HasDynamicInvoke > 0:
                fee += int(500 * 100000000 / self.ratio)  # if it has dynamic invoke, add extra 500 gas

            return fee

        if api_hash == HASH_SYSTEM_STORAGE_PUT or api_hash == HASH_SYSTEM_STORAGE_PUTEX or api_hash == HASH_NEO_STORAGE_PUT or api_hash == HASH_ANT_STORAGE_PUT:
            l1 = len(self.CurrentContext.EvaluationStack.Peek(1).GetByteArray())
            l2 = len(self.CurrentContext.EvaluationStack.Peek(2).GetByteArray())
            return (int((l1 + l2 - 1) / 1024) + 1) * 1000

        return 1

    @staticmethod
    def Run(snapshot, script, container=None, exit_on_error=False, gas=Fixed8.Zero(), test_mode=True, wb=None):
        """
        Runs a script in a test invoke environment

        Args:
            script (bytes): The script to run
            container (neo.Core.TX.Transaction): [optional] the transaction to use as the script container

        Returns:
            ApplicationEngine
        """

        engine = ApplicationEngine(TriggerType.Application, container, snapshot, gas, test_mode)

        # maybe not the best solution
        # but one for now
        if not wb:
            _script = binascii.unhexlify(script)
        else:
            _script = script

        engine.LoadScript(_script)
        engine.Execute()

        for event in engine._Service.events_to_dispatch:
            events.emit(event.event_type, event)

        return engine
