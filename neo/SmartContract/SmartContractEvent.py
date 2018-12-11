from neocore.IO.BinaryWriter import BinaryWriter
from neocore.IO.BinaryReader import BinaryReader
from neocore.UInt160 import UInt160
from neocore.BigInteger import BigInteger
from neocore.Cryptography.Crypto import Crypto
from neo.IO.MemoryStream import StreamManager
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neocore.IO.Mixins import SerializableMixin
import binascii
from neo.Core.State.ContractState import ContractState
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class SmartContractEvent(SerializableMixin):
    """
    SmartContractEvent is sent as argument to all smart contract event handlers. It
    includes all the information about the current event, such as type, payload,
    contract hash, transaction hash, and block number.

    - event_type (str)
    - contract_hash (UInt160)
    - tx_hash (UInt256)
    - block_number (int)
    - event_payload (object[])
    - execution_success (bool)
    - test_mode (bool)

    `event_payload` is always a list of object, depending on what data types you sent
    in the smart contract.
    """
    RUNTIME_NOTIFY = "SmartContract.Runtime.Notify"  # payload: object[]
    RUNTIME_LOG = "SmartContract.Runtime.Log"  # payload: bytes

    EXECUTION = "SmartContract.Execution.*"
    EXECUTION_INVOKE = "SmartContract.Execution.Invoke"
    EXECUTION_SUCCESS = "SmartContract.Execution.Success"
    EXECUTION_FAIL = "SmartContract.Execution.Fail"

    VERIFICATION = "SmartContract.Verification.*"
    VERIFICATION_SUCCESS = "SmartContract.Verification.Success"
    VERIFICATION_FAIL = "SmartContract.Verification.Fail"

    STORAGE = "SmartContract.Storage.*"
    STORAGE_GET = "SmartContract.Storage.Get"
    STORAGE_PUT = "SmartContract.Storage.Put"
    STORAGE_DELETE = "SmartContract.Storage.Delete"

    CONTRACT = "SmartContract.Contract.*"
    CONTRACT_CREATED = "SmartContract.Contract.Create"
    CONTRACT_MIGRATED = "SmartContract.Contract.Migrate"
    CONTRACT_DESTROY = "SmartContract.Contract.Destroy"

    event_type = None
    event_payload = None  # type:ContractParameter
    contract_hash = None
    block_number = None
    tx_hash = None
    execution_success = None
    test_mode = None

    contract = None
    token = None

    def __init__(self, event_type, event_payload, contract_hash, block_number, tx_hash, execution_success=False, test_mode=False):

        if event_payload and not isinstance(event_payload, ContractParameter):
            raise Exception("Event payload must be ContractParameter")

        self.event_type = event_type
        self.event_payload = event_payload
        self.contract_hash = contract_hash
        self.block_number = block_number
        self.tx_hash = tx_hash
        self.execution_success = execution_success
        self.test_mode = test_mode
        self.token = None

        if not self.event_payload:
            self.event_payload = ContractParameter(ContractParameterType.Array, value=[])

        if self.event_type in [SmartContractEvent.CONTRACT_CREATED, SmartContractEvent.CONTRACT_MIGRATED]:
            if self.event_payload.Type == ContractParameterType.InteropInterface:
                self.contract = self.event_payload.Value

    def Serialize(self, writer):
        writer.WriteVarString(self.event_type.encode('utf-8'))
        writer.WriteUInt160(self.contract_hash)
        writer.WriteUInt32(self.block_number)
        writer.WriteUInt256(self.tx_hash)
        self.SerializePayload(writer)

    def SerializePayload(self, writer):

        if self.event_type in [SmartContractEvent.CONTRACT_CREATED, SmartContractEvent.CONTRACT_MIGRATED] and self.contract:
            self.contract.Serialize(writer)
            if self.token:
                self.token.Serialize(writer)

    def Deserialize(self, reader):
        self.event_type = reader.ReadVarString().decode('utf-8')
        self.contract_hash = reader.ReadUInt160()
        self.block_number = reader.ReadUInt32()
        self.tx_hash = reader.ReadUInt256()
        self.DeserializePayload(reader)

    def DeserializePayload(self, reader):
        if self.event_type in [SmartContractEvent.CONTRACT_CREATED, SmartContractEvent.CONTRACT_MIGRATED]:
            self.contract = ContractState()
            self.contract.Deserialize(reader)
            try:
                from neo.Wallets.NEP5Token import NEP5Token
                token = NEP5Token(binascii.hexlify(self.contract.Code.Script))
                token.Deserialize(reader)
                self.token = token
            except Exception as e:
                logger.debug("Couldnt deserialize token %s " % e)

    def __str__(self):
        return "SmartContractEvent(event_type=%s, event_payload=%s, contract_hash=%s, block_number=%s, tx_hash=%s, execution_success=%s, test_mode=%s)" \
               % (self.event_type, self.event_payload, self.contract_hash, self.block_number, self.tx_hash, self.execution_success, self.test_mode)

    def ToByteArray(self):
        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        self.Serialize(writer)
        out = stream.getvalue()
        StreamManager.ReleaseStream(stream)
        return out

    @staticmethod
    def FromByteArray(data):
        stream = StreamManager.GetStream(data=data)
        reader = BinaryReader(stream)

        etype = reader.ReadVarString().decode('utf-8')
        reader.stream.seek(0)

        if etype == SmartContractEvent.RUNTIME_NOTIFY:
            event = NotifyEvent(None, None, None, None, None)
        else:
            event = SmartContractEvent(None, None, None, None, None)

        event.Deserialize(reader)
        StreamManager.ReleaseStream(stream)
        return event

    def CheckIsNEP5(self):
        if self.contract and self.contract.IsNEP5Contract:
            self.token = self.contract._nep_token

    def ToJson(self):

        jsn = {
            'type': self.event_type,
            'contract': self.contract_hash.To0xString(),
            'block': self.block_number,
            'tx': self.tx_hash.To0xString()
        }

        if self.event_type in [SmartContractEvent.CONTRACT_CREATED, SmartContractEvent.CONTRACT_MIGRATED]:
            jsn['contract'] = self.contract.ToJson()
            del jsn['contract']['script']

        if self.token:
            jsn['token'] = self.token.ToJson()

        return jsn


class NotifyType:
    TRANSFER = b'transfer'  # OnTransfer = RegisterAction('transfer', 'to', 'from', 'amount')
    APPROVE = b'approve'  # OnApprove = RegisterAction('approve', 'addr_from', 'addr_to', 'amount')
    REFUND = b'refund'  # OnRefund = RegisterAction('refund', 'to', 'amount')
    MINT = b'mint'  # OnMint = RegisterAction('mint', 'addr_to', 'amount')


class NotifyEvent(SmartContractEvent):
    notify_type = None

    addr_to = None
    addr_from = None
    amount = 0

    is_standard_notify = False

    @property
    def ShouldPersist(self):
        return self.is_standard_notify and not self.test_mode

    @property
    def Type(self):
        return self.notify_type.decode('utf-8')

    @property
    def AddressTo(self):
        if self.addr_to:
            return Crypto.ToAddress(self.addr_to)
        return None

    @property
    def AddressFrom(self):
        if self.addr_from:
            return Crypto.ToAddress(self.addr_from)
        return None

    @property
    def Contract(self):
        return self.contract_hash

    @property
    def Amount(self):
        return self.amount

    def __init__(self, event_type, event_payload, contract_hash, block_number, tx_hash, execution_success=False, test_mode=False):
        super(NotifyEvent, self).__init__(event_type, event_payload, contract_hash, block_number, tx_hash, execution_success, test_mode)

        self.is_standard_notify = False

        if self.event_payload.Type == ContractParameterType.Array and len(self.event_payload.Value) > 0:

            payload = self.event_payload.Value
            plen = len(payload)

            self.notify_type = payload[0].Value

            empty = UInt160(data=bytearray(20))
            try:
                if plen == 4 and self.notify_type in [NotifyType.TRANSFER, NotifyType.APPROVE]:
                    if payload[1].Value is None:
                        self.addr_from = empty
                        logger.debug("Using contract addr from address %s " % self.event_payload)
                    elif payload[1].Value is False:
                        logger.debug("Using contract addr from address %s " % self.event_payload)
                        self.addr_from = empty
                    else:
                        self.addr_from = UInt160(data=payload[1].Value) if len(payload[1].Value) == 20 else empty
                    self.addr_to = UInt160(data=payload[2].Value) if len(payload[2].Value) == 20 else empty
                    self.amount = int(BigInteger.FromBytes(payload[3].Value)) if isinstance(payload[3].Value, (bytes, bytearray)) else int(payload[3].Value)
                    self.is_standard_notify = True

                elif self.notify_type == NotifyType.REFUND and plen >= 3:  # Might have more arguments
                    self.addr_to = UInt160(data=payload[1].Value) if len(payload[1].Value) == 20 else empty
                    self.amount = int(BigInteger.FromBytes(payload[2].Value)) if isinstance(payload[2].Value, (bytes, bytearray)) else int(payload[2].Value)
                    self.addr_from = self.contract_hash
                    self.is_standard_notify = True

                elif self.notify_type == NotifyType.MINT and plen == 3:
                    self.addr_to = UInt160(data=payload[1].Value) if len(payload[1].Value) == 20 else empty
                    self.amount = int(BigInteger.FromBytes(payload[2].Value)) if isinstance(payload[2].Value, (bytes, bytearray)) else int(payload[2].Value)
                    self.addr_from = self.contract_hash
                    self.is_standard_notify = True

            except Exception as e:
                logger.debug("Could not determine notify event: %s %s" % (e, self.event_payload))

        elif self.event_payload.Type == ContractParameterType.String:
            self.notify_type = self.event_payload.Value

    #        else:
    #            logger.debug("NOTIFY %s %s" % (self.event_payload.Type, self.event_payload.Value))

    def SerializePayload(self, writer):

        writer.WriteVarString(self.notify_type)

        if self.is_standard_notify:
            writer.WriteUInt160(self.addr_from)
            writer.WriteUInt160(self.addr_to)

            if self.Amount < 0:
                logger.debug("Transfer Amount less than 0")
                writer.WriteVarInt(0)
            elif self.Amount < 0xffffffffffffffff:
                writer.WriteVarInt(self.amount)
            else:
                logger.debug("Writing Payload value amount greater than ulong long is not allowed.  Setting to ulong long max")
                writer.WriteVarInt(0xffffffffffffffff)

    def DeserializePayload(self, reader):
        try:
            self.notify_type = reader.ReadVarString()
        except Exception as e:
            logger.debug("Could not read notify type")

        if self.notify_type in [NotifyType.REFUND, NotifyType.APPROVE, NotifyType.TRANSFER]:
            try:
                self.addr_from = reader.ReadUInt160()
                self.addr_to = reader.ReadUInt160()
                self.amount = reader.ReadVarInt()
                self.is_standard_notify = True
            except Exception as e:
                logger.debug("Could not transfer notification data")

    def ToJson(self):
        jsn = super(NotifyEvent, self).ToJson()
        jsn['notify_type'] = self.Type
        jsn['addr_to'] = self.AddressTo
        jsn['addr_from'] = self.AddressFrom
        jsn['amount'] = "%s" % self.Amount
        return jsn
