from neo.Blockchain import GetBlockchain as BC
from neo.Core.Helper import Helper
from neocore.Cryptography.Crypto import Crypto
from neocore.UInt160 import UInt160
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Network.NodeLeader import NodeLeader

from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage

from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neocore.Fixed8 import Fixed8
from logzero import logger
from neo.contrib.smartcontract import SmartContract
from twisted.internet import reactor

from neo.VM.OpCode import PACK

import os
import binascii
import json


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class SaleMonitor:
    TXNS = []
    TXN_COUNT = 0
    REGISTERED = []
    ADDR_TOTAL = 0


def setupSale(wallet, args):

    contract = BC().GetContract(args[0])

    smart_contract = SmartContract(contract.Code.ScriptHash().ToString())

    @smart_contract.on_notify
    def sc_notify(event):
        # Make sure that the event payload list has at least one element.
        if not len(event.event_payload):
            return

        etype = event.event_payload[0].decode("utf-8")
        if etype == 'kyc_registration':
            registered = event.event_payload[1]
            uint = UInt160(data=registered)
            registered_addr = Crypto.ToAddress(uint)
            SaleMonitor.REGISTERED.append(registered_addr)
            logger.info("Register count %s " % len(SaleMonitor.REGISTERED))

            if len(SaleMonitor.REGISTERED) == SaleMonitor.ADDR_TOTAL:
                logger.info("Registrations complete!")

    file_name = args[1]
    roundNo = args[2]
    perTX = int(args[3])
    file = open(file_name, 'r')
    address_list = json.load(file)

    logger.info("round: %s %s" % (roundNo, perTX))
    logger.info("total addr %s " % len(address_list))
    SaleMonitor.ADDR_TOTAL = len(address_list)

    divided_in_chunks = list(chunks(address_list, perTX))

    txns = []
    for addrlist in divided_in_chunks:
        tx = make_tx(addrlist, roundNo, contract, wallet)
        txns.append(tx)

    def send_things():
        mcount = 0
        while len(txns) and mcount < 20:
            tx = txns.pop(0)
            res = NodeLeader.Instance().Relay(tx)
            mcount += 1
            if mcount == 20:
                reactor.callLater(20, send_things)

    send_things()


def make_tx(addrlist, roundNo, contract, wallet):

    sb = ScriptBuilder()

    for addr in addrlist:
        addr_hash = Helper.AddrStrToScriptHash(addr).Data
        sb.push(addr_hash)
    sb.push(len(addrlist))
    sb.Emit(PACK)
    sb.push(roundNo.encode('utf-8').hex())
    sb.push(2)
    sb.Emit(PACK)
    sb.push(b'putWhitelist'.hex())
    sb.EmitAppCall(contract.Code.ScriptHash().Data)
    script = sb.ToArray()

    tx = InvocationTransaction(inputs=[], outputs=[],)
    tx.Version = 1
    tx.Script = binascii.unhexlify(script)
    tx.Gas = Fixed8.Zero()

    attr = bytearray(os.urandom(20))
    tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Remark4, data=attr)]

    contract = wallet.GetDefaultContract()
    tx.Attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=contract.ScriptHash))

    context = ContractParametersContext(tx)
    wallet.Sign(context)
    tx.scripts = context.GetScripts()

    return tx
