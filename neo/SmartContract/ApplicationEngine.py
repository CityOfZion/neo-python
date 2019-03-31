import binascii
import datetime

from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Fixed8 import Fixed8
from neo.Core.UInt160 import UInt160

from neo.Core.State.AccountState import AccountState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ContractState import ContractPropertyState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.ValidatorState import ValidatorState
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
# used for ApplicationEngine.Run
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Settings import settings
from neo.SmartContract import TriggerType
from neo.VM import OpCode
from neo.VM import VMState
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.InteropService import Array
from neo.VM.OpCode import APPCALL, TAILCALL, \
    SYSCALL, NOP, SHA256, SHA1, HASH160, HASH256, CHECKSIG, CHECKMULTISIG
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

    def GasConsumed(self):
        return Fixed8(self.gas_consumed)

    def __init__(self, trigger_type, container, table, service, gas, testMode=False, exit_on_error=False):

        super(ApplicationEngine, self).__init__(container=container, crypto=Crypto.Default(), table=table, service=service, exit_on_error=exit_on_error)

        self.Trigger = trigger_type
        self.gas_amount = self.gas_free + gas.value
        self.testMode = testMode
        self._is_stackitem_count_strict = True

    def CheckDynamicInvoke(self, opcode):
        cx = self.CurrentContext

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

    def PreStepInto(self, opcode):
        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            return True
        self.gas_consumed = self.gas_consumed + (self.GetPrice() * self.ratio)
        if not self.testMode and self.gas_consumed > self.gas_consumed:
            return False
        if self.testMode and self.ops_processed > self.max_free_ops:
            logger.debug("Too many free operations processed")
            return False
        try:
            if not self.CheckDynamicInvoke(opcode):
                return False
        except Exception:
            pass
        return True

    # @profile_it
    def Execute(self):
        try:
            if settings.log_vm_instructions:
                self.log_file = open(self.log_file_name, 'w')
                self.write_log(str(datetime.datetime.now()))

            while True:
                if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
                    nextOpcode = OpCode.RET
                else:
                    nextOpcode = self.CurrentContext.NextInstruction

                if not self.PreStepInto(nextOpcode):
                    # TODO: check with NEO is this should now be changed to not use |=
                    self._VMState |= VMState.FAULT
                    return False
                self.StepInto()
                if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0:
                    break
        except Exception:
            self._VMState |= VMState.FAULT
            return False
        finally:
            if self.log_file:
                self.log_file.close()

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
