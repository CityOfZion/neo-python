import binascii
from logzero import logger

from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.OpCode import CALL, APPCALL, CHECKSIG, HASH160, HASH256, NOP, SHA1, SHA256, DEPTH, DUP, PACK, TUCK, OVER, \
    SYSCALL, TAILCALL, NEWARRAY, NEWSTRUCT, PUSH16, UNPACK, CAT, CHECKMULTISIG, PUSHDATA4
from neo.VM import VMState
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

from neocore.UInt160 import UInt160
import datetime
from neo.Settings import settings


class ApplicationEngine(ExecutionEngine):
    ratio = 100000
    gas_free = 10 * 100000000
    gas_amount = 0
    gas_consumed = 0
    testMode = False

    Trigger = None

    def GasConsumed(self):
        return Fixed8(self.gas_consumed)

    def __init__(self, trigger_type, container, table, service, gas, testMode=False, exit_on_error=False):

        super(ApplicationEngine, self).__init__(container=container, crypto=Crypto.Default(), table=table, service=service, exit_on_error=exit_on_error)

        self.Trigger = trigger_type
        self.gas_amount = self.gas_free + gas.value
        self.testMode = testMode

    def CheckArraySize(self):

        maxArraySize = 1024
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode in [PACK, NEWARRAY, NEWSTRUCT]:

            size = self.EvaluationStack.Peek().GetBigInteger()

            if size > maxArraySize:
                logger.error("ARRAY SIZE TOO BIG!!!")
                return False

            return True

        return True

    def CheckInvocationStack(self):

        maxInvocationStackSize = 1024
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode == CALL or opcode == APPCALL:
            if self.InvocationStack.Count >= maxInvocationStackSize:
                logger.error("INVOCATION STACK TOO BIG, RETURN FALSE")
                return False

            return True

        return True

    def CheckItemSize(self):

        maxItemSize = 1024 * 1024
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode == PUSHDATA4:

            if cx.InstructionPointer + 4 >= len(cx.Script):
                return False

            # TODO this should be double checked.  it has been
            # double checked and seems to work, but could possibly not work
            position = cx.InstructionPointer + 1
            lengthpointer = cx.Script[position:position + 4]
            length = int.from_bytes(lengthpointer, 'little')

            if length > maxItemSize:
                logger.error("ITEM IS GREATER THAN MAX ITEM SIZE!")
                return False

            return True

        elif opcode == CAT:

            if self.EvaluationStack.Count < 2:
                logger.error("NOT ENOUGH ITEMS TO CONCAT")
                return False

            length = 0

            try:
                length = len(self.EvaluationStack.Peek(0).GetByteArray()) + len(self.EvaluationStack.Peek(1).GetByteArray())
            except Exception as e:
                logger.error("COULD NOT GET STR LENGTH!")
                raise e

            if length > maxItemSize:
                logger.error("ITEM IS GREATER THAN MAX SIZE!!!")
                return False

            return True

        return True

    def CheckStackSize(self):

        maxStackSize = 2 * 1024
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        size = 0

        opcode = cx.NextInstruction

        if opcode < PUSH16:
            size = 1

        else:

            if opcode in [DEPTH, DUP, OVER, TUCK]:
                size = 1

            elif opcode == UNPACK:

                item = self.EvaluationStack.Peek()

                if not item.IsArray:
                    logger.error("ITEM NOT ARRAY:")
                    return False

                size = len(item.GetArray())

        if size == 0:
            return True

        size += self.EvaluationStack.Count + self.AltStack.Count

        if size > maxStackSize:
            logger.error("SIZE IS OVER MAX STACK SIZE!!!!")
            return False

        return True

    def CheckDynamicInvoke(self):
        cx = self.CurrentContext

        if cx.InstructionPointer >= len(cx.Script):
            return True

        opcode = cx.NextInstruction

        if opcode == APPCALL:
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

        return True

    # @profile_it
    def Execute(self):
        def loop_validation_and_stepinto():
            while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0:

                try:

                    self.gas_consumed = self.gas_consumed + (self.GetPrice() * self.ratio)
                #                print("gas consumeb: %s " % self.gas_consumed)
                except Exception as e:
                    logger.error("Exception calculating gas consumed %s " % e)
                    self._VMState |= VMState.FAULT
                    return False

                if not self.testMode and self.gas_consumed > self.gas_amount:
                    logger.error("NOT ENOUGH GAS")
                    self._VMState |= VMState.FAULT
                    return False

                if not self.CheckItemSize():
                    logger.error("ITEM SIZE TOO BIG")
                    self._VMState |= VMState.FAULT
                    return False

                if not self.CheckStackSize():
                    logger.error("STACK SIZE TOO BIG")
                    self._VMState |= VMState.FAULT
                    return False

                if not self.CheckArraySize():
                    logger.error("ARRAY SIZE TOO BIG")
                    self._VMState |= VMState.FAULT
                    return False

                if not self.CheckInvocationStack():
                    logger.error("INVOCATION SIZE TO BIIG")
                    self._VMState |= VMState.FAULT
                    return False

                if not self.CheckDynamicInvoke():
                    logger.error("Dynamic invoke without proper contract")
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

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
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

        strbytes = self.CurrentContext.Script[self.CurrentContext.InstructionPointer + 2:length + self.CurrentContext.InstructionPointer + 2]

        api_name = strbytes.decode('utf-8')

        api = api_name.replace('Antshares.', 'Neo.')

        if api == "Neo.Runtime.CheckWitness":
            return 200

        elif api == "Neo.Blockchain.GetHeader":
            return 100

        elif api == "Neo.Blockchain.GetBlock":
            return 200

        elif api == "Neo.Runtime.GetTime":
            return 100

        elif api == "Neo.Blockchain.GetTransaction":
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

        elif api == "Neo.Transaction.GetUnspentCoins":
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

            fee = int(100 * 100000000 / self.ratio)  # 100 gas for contract with no storage no dynamic invoke

            contract_properties = self.EvaluationStack.Peek(3).GetBigInteger()

            if contract_properties & ContractPropertyState.HasStorage > 0:
                fee += int(400 * 100000000 / self.ratio)  # if contract has storage, we add 400 gas

            if contract_properties & ContractPropertyState.HasDynamicInvoke > 0:
                fee += int(500 * 100000000 / self.ratio)  # if it has dynamic invoke, add extra 500 gas

            return fee

        elif api == "Neo.Storage.Get":
            return 100

        elif api == "Neo.Storage.Put":
            l1 = len(self.EvaluationStack.Peek(1).GetByteArray())
            l2 = len(self.EvaluationStack.Peek(2).GetByteArray())
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
        sn = bc._db.snapshot()

        accounts = DBCollection(bc._db, sn, DBPrefix.ST_Account, AccountState)
        assets = DBCollection(bc._db, sn, DBPrefix.ST_Asset, AssetState)
        validators = DBCollection(bc._db, sn, DBPrefix.ST_Validator, ValidatorState)
        contracts = DBCollection(bc._db, sn, DBPrefix.ST_Contract, ContractState)
        storages = DBCollection(bc._db, sn, DBPrefix.ST_Storage, StorageItem)

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

        engine.LoadScript(script, False)

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
