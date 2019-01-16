import binascii
import sys
from collections import deque
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM import OpCode
from neo.VM.OpCode import PACK, NEWARRAY, NEWSTRUCT, SETITEM, APPEND, CALL, APPCALL, PUSHDATA4, CAT, PUSH16, TAILCALL, \
    SYSCALL, NOP, SHA256, SHA1, HASH160, HASH256, CHECKSIG, CHECKMULTISIG
from neo.VM import VMState
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM.InteropService import CollectionMixin, Map, Array
from neocore.Cryptography.Crypto import Crypto
from neocore.Fixed8 import Fixed8

# used for ApplicationEngine.Run
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.ContractState import ContractPropertyState
from neo.SmartContract import TriggerType
from neo.VM.InteropService import Array
from neocore.UInt160 import UInt160
import datetime
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class ApplicationEngine(ExecutionEngine):
    ratio = 100000
    gas_free = 10 * 100000000
    gas_amount = 0
    gas_consumed = 0
    testMode = False

    Trigger = None

    invocation_args = None

    max_free_ops = 500000

    maxItemSize = 1024 * 1024
    maxArraySize = 1024
    max_shl_shr = 65535  # ushort.maxValue
    min_shl_shr = -65535  # -ushort.maxValue
    MaxSizeForBigInteger = 32

    def GasConsumed(self):
        return Fixed8(self.gas_consumed)

    def __init__(self, trigger_type, container, table, service, gas, testMode=False, exit_on_error=False):

        super(ApplicationEngine, self).__init__(container=container, crypto=Crypto.Default(), table=table, service=service, exit_on_error=exit_on_error)

        self.Trigger = trigger_type
        self.gas_amount = self.gas_free + gas.value
        self.testMode = testMode
        self._is_stackitem_count_strict = True

    def CheckArraySize(self):
        cx = self.CurrentContext

        opcode = cx.NextInstruction

        if opcode in [PACK, NEWARRAY, NEWSTRUCT]:
            if cx.EvaluationStack.Count == 0:
                return False
            size = cx.EvaluationStack.Peek().GetBigInteger()

        elif opcode == SETITEM:
            if cx.EvaluationStack.Count < 3:
                return False

            map_stackitem = cx.EvaluationStack.Peek(2)
            if not isinstance(map_stackitem, Map):
                return True

            key = cx.EvaluationStack.Peek(1)
            if isinstance(key, CollectionMixin):
                return False

            if map_stackitem.ContainsKey(key):
                return True
            size = map_stackitem.Count + 1

        elif opcode == APPEND:
            if cx.EvaluationStack.Count < 2:
                return False

            collection: Array = cx.EvaluationStack.Peek(1)
            if not isinstance(collection, Array):
                return False
            size = collection.Count + 1
        else:
            return True

        return size <= self.maxArraySize

    def CheckInvocationStack(self):

        maxInvocationStackSize = 1024
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode == CALL or opcode == APPCALL:
            if self.InvocationStack.Count >= maxInvocationStackSize:
                logger.debug("INVOCATION STACK TOO BIG, RETURN FALSE")
                return False

            return True

        return True

    def _checkBigInteger(self, value):
        return len(value.ToByteArray()) <= self.MaxSizeForBigInteger

    def CheckBigIntegers(self):
        cx = self.CurrentContext
        opcode = cx.NextInstruction

        if opcode == OpCode.SHL:
            ishift = cx.EvaluationStack.Peek(0).GetBigInteger()

            if ishift > self.max_shl_shr or ishift < self.min_shl_shr:
                return False

            x = cx.EvaluationStack.Peek(1).GetBigInteger()

            try:
                if not self._checkBigInteger(x << ishift):
                    return False
            except ValueError:
                # negative ishift throws a value error
                return False

        if opcode == OpCode.SHR:
            ishift = cx.EvaluationStack.Peek(0).GetBigInteger()

            if ishift > self.max_shl_shr or ishift < self.min_shl_shr:
                return False

            x = cx.EvaluationStack.Peek(1).GetBigInteger()

            try:
                if not self._checkBigInteger(x >> ishift):
                    return False
            except ValueError:
                # negative ishift throws a value error
                return False

        if opcode == OpCode.INC:
            x = cx.EvaluationStack.Peek().GetBigInteger()
            if not self._checkBigInteger(x) or not self._checkBigInteger(x + 1):
                return False

        if opcode == OpCode.DEC:
            x = cx.EvaluationStack.Peek().GetBigInteger()
            if not self._checkBigInteger(x) or (x.Sign <= 0 and not self._checkBigInteger(x - 1)):
                return False

        if opcode == OpCode.ADD:
            x2 = cx.EvaluationStack.Peek().GetBigInteger()
            x1 = cx.EvaluationStack.Peek(1).GetBigInteger()

            if not self._checkBigInteger(x2) or not self._checkBigInteger(x1) or not self._checkBigInteger(x1 + x2):
                return False

        if opcode == OpCode.SUB:
            x2 = cx.EvaluationStack.Peek().GetBigInteger()
            x1 = cx.EvaluationStack.Peek(1).GetBigInteger()

            if not self._checkBigInteger(x2) or not self._checkBigInteger(x1) or not self._checkBigInteger(x1 - x2):
                return False

        if opcode == OpCode.MUL:
            x2 = cx.EvaluationStack.Peek().GetBigInteger()
            x1 = cx.EvaluationStack.Peek(1).GetBigInteger()

            length_x1 = len(x1.ToByteArray())
            if length_x1 > self.MaxSizeForBigInteger:
                return False

            length_x2 = len(x2.ToByteArray())
            if length_x2 > self.MaxSizeForBigInteger:
                return False

            if length_x1 + length_x2 > self.MaxSizeForBigInteger:
                return False

        if opcode in [OpCode.DIV, OpCode.MOD]:
            x2 = cx.EvaluationStack.Peek().GetBigInteger()
            x1 = cx.EvaluationStack.Peek(1).GetBigInteger()

            if not self._checkBigInteger(x2) or not self._checkBigInteger(x1):
                return False

        return True

    def CheckItemSize(self):

        cx = self.CurrentContext
        opcode = cx.NextInstruction

        if opcode == PUSHDATA4:

            if cx.InstructionPointer + 4 >= len(cx.Script):
                return False

            # TODO this should be double checked.  it has been
            # double checked and seems to work, but could possibly not work
            position = cx.InstructionPointer + 1
            lengthpointer = cx.Script[position:position + 4]
            length = int.from_bytes(lengthpointer, 'little')

            if length > self.maxItemSize:
                logger.debug("ITEM IS GREATER THAN MAX ITEM SIZE!")
                return False

            return True

        elif opcode == CAT:

            if cx.EvaluationStack.Count < 2:
                logger.debug("NOT ENOUGH ITEMS TO CONCAT")
                return False

            length = 0

            try:
                length = len(cx.EvaluationStack.Peek(0).GetByteArray()) + len(cx.EvaluationStack.Peek(1).GetByteArray())
            except Exception as e:
                logger.debug("COULD NOT GET STR LENGTH!")
                raise e

            if length > self.maxItemSize:
                logger.debug("ITEM IS GREATER THAN MAX SIZE!!!")
                return False

            return True

        return True

    def CheckStackSize(self):
        maxStackSize = 2 * 1024

        size = 0
        cx = self.CurrentContext
        opcode = cx.NextInstruction

        if opcode <= PUSH16:
            size += 1
        else:
            if opcode in [OpCode.JMPIF, OpCode.JMPIFNOT, OpCode.DROP, OpCode.NIP, OpCode.EQUAL, OpCode.BOOLAND, OpCode.BOOLOR, OpCode.CHECKMULTISIG,
                          OpCode.REVERSE, OpCode.HASKEY, OpCode.THROWIFNOT]:
                size -= 1
                self._is_stackitem_count_strict = False
            elif opcode in [OpCode.XSWAP, OpCode.ROLL, OpCode.CAT, OpCode.LEFT, OpCode.RIGHT, OpCode.AND, OpCode.OR, OpCode.XOR, OpCode.ADD, OpCode.SUB,
                            OpCode.MUL, OpCode.DIV, OpCode.SHL, OpCode.SHR, OpCode.NUMEQUAL, OpCode.NUMNOTEQUAL, OpCode.LT, OpCode.GT, OpCode.LTE, OpCode.GTE,
                            OpCode.MIN, OpCode.MAX, OpCode.CHECKSIG, OpCode.CALL_ED, OpCode.CALL_EDT]:
                size -= 1
            elif opcode in [OpCode.RET, OpCode.APPCALL, OpCode.TAILCALL, OpCode.NOT, OpCode.ARRAYSIZE]:
                self._is_stackitem_count_strict = False
            elif opcode in [OpCode.SYSCALL, OpCode.PICKITEM, OpCode.SETITEM, OpCode.APPEND, OpCode.VALUES]:
                size = sys.maxsize
                self._is_stackitem_count_strict = False
            elif opcode in [OpCode.DUPFROMALTSTACK, OpCode.DEPTH, OpCode.DUP, OpCode.OVER, OpCode.TUCK, OpCode.NEWMAP]:
                size += 1
            elif opcode in [OpCode.XDROP, OpCode.REMOVE]:
                size -= 2
                self._is_stackitem_count_strict = False
            elif opcode in [OpCode.SUBSTR, OpCode.WITHIN, OpCode.VERIFY]:
                size -= 2
            elif opcode == OpCode.UNPACK:
                size += self.CurrentContext.EvaluationStack.Peek().GetBigInteger
                self._is_stackitem_count_strict = False
            elif opcode in [OpCode.NEWARRAY, OpCode.NEWSTRUCT]:
                size += self.CurrentContext.EvaluationStack.Peek().Count
            elif opcode == OpCode.KEYS:
                size += self.CurrentContext.EvaluationStack.Peek().Count
                self._is_stackitem_count_strict = False

        if size <= maxStackSize:
            return True

        if self._is_stackitem_count_strict:
            return False

        stack_item_list = []
        for execution_context in self.InvocationStack.Items:  # type: ExecutionContext
            stack_item_list += execution_context.EvaluationStack.Items + execution_context.AltStack.Items

        stackitem_count = self.GetItemCount(stack_item_list)
        if stackitem_count > maxStackSize:
            return False

        self._is_stackitem_count_strict = True
        return True

    def GetItemCount(self, items_list):  # list of StackItems
        count = 0
        items = deque(items_list)
        while items:
            stackitem = items.pop()
            if isinstance(stackitem, Map):
                items.extend(stackitem.Values)
                continue

            if isinstance(stackitem, Array):
                items.extend(stackitem.GetArray())
                continue
            count += 1

        return count

    def CheckDynamicInvoke(self):
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode in [OpCode.APPCALL, OpCode.TAILCALL]:
            opreader = cx.OpReader
            # read the current position of the stream
            start_pos = opreader.stream.tell()

            # normal app calls are stored in the op reader
            # we read ahead past the next instruction 1 the next 20 bytes
            script_hash = opreader.ReadBytes(21)[1:]

            # then reset the position
            opreader.stream.seek(start_pos)

            for b in script_hash:
                # if any of the bytes are greater than 0, this is a normal app call
                if b > 0:
                    return True

            # if this is a dynamic app call, we will arrive here
            # get the current executing script hash
            current = UInt160(data=cx.ScriptHash())
            current_contract_state = self._Table.GetContractState(current.ToBytes())

            # if current contract state cant do dynamic calls, return False
            return current_contract_state.HasDynamicInvoke
        elif opcode in [OpCode.CALL_ED, OpCode.CALL_EDT]:
            current = UInt160(data=cx.ScriptHash())
            current_contract_state = self._Table.GetContractState(current.ToBytes())
            return current_contract_state.HasDynamicInvoke

        else:
            return True

    # @profile_it
    def Execute(self):
        def loop_validation_and_stepinto():
            while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0:
                if self.CurrentContext.InstructionPointer < len(self.CurrentContext.Script):
                    try:
                        self.gas_consumed = self.gas_consumed + (self.GetPrice() * self.ratio)
                    except Exception as e:
                        logger.debug("Exception calculating gas consumed %s " % e)
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.testMode and self.gas_consumed > self.gas_amount:
                        logger.debug("NOT ENOUGH GAS")
                        self._VMState |= VMState.FAULT
                        return False

                    if self.testMode and self.ops_processed > self.max_free_ops:
                        logger.debug("Too many free operations processed")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckItemSize():
                        logger.debug("ITEM SIZE TOO BIG")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckStackSize():
                        logger.debug("STACK SIZE TOO BIG")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckArraySize():
                        logger.debug("ARRAY SIZE TOO BIG")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckInvocationStack():
                        logger.debug("INVOCATION SIZE TO BIG")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckBigIntegers():
                        logger.debug("BigIntegers check failed")
                        self._VMState |= VMState.FAULT
                        return False

                    if not self.CheckDynamicInvoke():
                        logger.debug("Dynamic invoke without proper contract")
                        self._VMState |= VMState.FAULT
                        return False

                self.StepInto()

        if settings.log_vm_instructions:
            with open(self.log_file_name, 'w') as self.log_file:
                self.write_log(str(datetime.datetime.now()))
                loop_validation_and_stepinto()
        else:
            loop_validation_and_stepinto()

        return not self._VMState & VMState.FAULT > 0

    def GetPrice(self):

        opcode = self.CurrentContext.NextInstruction

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
        elif opcode == CHECKSIG:
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

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script) - 3:
            return 1

        length = self.CurrentContext.Script[self.CurrentContext.InstructionPointer + 1]

        if self.CurrentContext.InstructionPointer > len(self.CurrentContext.Script) - length - 2:
            return 1

        strbytes = self.CurrentContext.Script[self.CurrentContext.InstructionPointer + 2:length + self.CurrentContext.InstructionPointer + 2]

        api_name = strbytes.decode('utf-8')

        api = api_name.replace('Antshares.', 'Neo.')
        api = api.replace('System.', 'Neo.')

        if api == "Neo.Runtime.CheckWitness":
            return 200

        elif api == "Neo.Blockchain.GetHeader":
            return 100

        elif api == "Neo.Blockchain.GetBlock":
            return 200

        elif api == "Neo.Blockchain.GetTransaction":
            return 100

        elif api == "Neo.Blockchain.GetTransactionHeight":
            return 100

        elif api == "Neo.Blockchain.GetAccount":
            return 100

        elif api == "Neo.Blockchain.GetValidators":
            return 200

        elif api == "Neo.Blockchain.GetAsset":
            return 100

        elif api == "Neo.Blockchain.GetContract":
            return 100

        elif api == "Neo.Transaction.GetReferences":
            return 200

        elif api == "Neo.Transaction.GetWitnesses":
            return 200

        elif api == "Neo.Transaction.GetUnspentCoins":
            return 200

        elif api in ["Neo.Witness.GetInvocationScript", "Neo.Witness.GetVerificationScript"]:
            return 100

        elif api == "Neo.Account.SetVotes":
            return 1000

        elif api == "Neo.Validator.Register":
            return int(1000 * 100000000 / self.ratio)

        elif api == "Neo.Asset.Create":
            return int(5000 * 100000000 / self.ratio)

        elif api == "Neo.Asset.Renew":
            return int(self.CurrentContext.EvaluationStack.Peek(1).GetBigInteger() * 5000 * 100000000 / self.ratio)

        elif api == "Neo.Contract.Create" or api == "Neo.Contract.Migrate":

            fee = int(100 * 100000000 / self.ratio)  # 100 gas for contract with no storage no dynamic invoke

            contract_properties = self.CurrentContext.EvaluationStack.Peek(3).GetBigInteger()

            if contract_properties & ContractPropertyState.HasStorage > 0:
                fee += int(400 * 100000000 / self.ratio)  # if contract has storage, we add 400 gas

            if contract_properties & ContractPropertyState.HasDynamicInvoke > 0:
                fee += int(500 * 100000000 / self.ratio)  # if it has dynamic invoke, add extra 500 gas

            return fee

        elif api == "Neo.Storage.Get":
            return 100

        elif api == "Neo.Storage.Put":
            l1 = len(self.CurrentContext.EvaluationStack.Peek(1).GetByteArray())
            l2 = len(self.CurrentContext.EvaluationStack.Peek(2).GetByteArray())
            return (int((l1 + l2 - 1) / 1024) + 1) * 1000

        elif api == "Neo.Storage.Delete":
            return 100

        return 1

    @staticmethod
    def Run(script, container=None, exit_on_error=False, gas=Fixed8.Zero(), test_mode=True):
        """
        Runs a script in a test invoke environment

        Args:
            script (bytes): The script to run
            container (neo.Core.TX.Transaction): [optional] the transaction to use as the script container

        Returns:
            ApplicationEngine
        """

        from neo.Core.Blockchain import Blockchain
        from neo.SmartContract.StateMachine import StateMachine
        from neo.EventHub import events

        bc = Blockchain.Default()

        accounts = DBCollection(bc._db, DBPrefix.ST_Account, AccountState)
        assets = DBCollection(bc._db, DBPrefix.ST_Asset, AssetState)
        validators = DBCollection(bc._db, DBPrefix.ST_Validator, ValidatorState)
        contracts = DBCollection(bc._db, DBPrefix.ST_Contract, ContractState)
        storages = DBCollection(bc._db, DBPrefix.ST_Storage, StorageItem)

        script_table = CachedScriptTable(contracts)
        service = StateMachine(accounts, validators, assets, contracts, storages, None)

        engine = ApplicationEngine(
            trigger_type=TriggerType.Application,
            container=container,
            table=script_table,
            service=service,
            gas=gas,
            testMode=test_mode,
            exit_on_error=exit_on_error
        )

        script = binascii.unhexlify(script)

        engine.LoadScript(script)

        try:
            success = engine.Execute()
            engine.testMode = True
            service.ExecutionCompleted(engine, success)
        except Exception as e:
            engine.testMode = True
            service.ExecutionCompleted(engine, False, e)

        for event in service.events_to_dispatch:
            events.emit(event.event_type, event)

        return engine
