# -*- coding:utf-8 -*-
"""
Description:
    UserWallet
"""


from AntShares.Core.TransactionAttribute import TransactionAttribute
from AntShares.Core.TransactionAttributeUsage import TransactionAttributeUsage
from AntShares.Core.Transaction import Transaction
from AntShares.Core.RegisterTransaction import RegisterTransaction
from AntShares.Core.IssueTransaction import IssueTransaction
from AntShares.Core.AssetType import AssetType
from AntShares.Wallets.Wallet import *
from AntShares.Wallets.Coin import Coin
from AntShares.Wallets.CoinState import CoinState

from AntShares.Helper import ANTCOIN
from AntShares.Exceptions import *

from AntShares.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet


def transfer(work_id, target_work_id, value, remark=None, asset=ANTCOIN):
    wallet_db = IndexedDBWallet()

    my_account = wallet_db.queryAccount(work_id=work_id)
    target_account = wallet_db.queryAccount(work_id=target_work_id)

    if my_account == None:
        raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % work_id)
    elif target_account == None:
        raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % target_work_id)


    part_my = Account(privateKey=my_account['pri_key'])
    pary_target = Account(privateKey=target_account['pri_key'])

    wallet = Wallet()

    inputs = []
    outputs = [TransactionOutput(AssetId=asset, Value=str(value), ScriptHash=pary_target.scriptHash)]
    if remark:
        attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Remark,
                                           data=remark)]
    else:
        attributes = []
    tx = Transaction(inputs, outputs, attributes)

    txid = wallet.makeTransaction(tx, part_my)
    print(txid)

    # TODO: update coin status
    pass

    return 0x0000

def transfer_mult(work_id, target, asset):
    """target format: {work_id: value}"""
    wallet_db = IndexedDBWallet()

    my_account = wallet_db.queryAccount(work_id=work_id)

    if my_account == None:
        raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % work_id)

    if not isinstance(target, dict):
        raise ValueError('Target format should be {work_id: value}.')

    for target_work_id in target.keys():
        target_account = wallet_db.queryAccount(work_id=target_work_id)
        if target_account == None:
            raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % target_work_id)

    part_my = Account(privateKey=my_account['pri_key'])
    wallet = Wallet()

    inputs = []
    outputs = [TransactionOutput(AssetId=asset, Value=str(value),
                                 ScriptHash=wallet_db.queryAccount(work_id=target_work_id).scriptHash)
               for target_work_id, value in target.iteritems]

    tx = Transaction(inputs, outputs)
    try:
        txid = wallet.makeTransaction(tx, part_my)
    except Exception as e:
        print(e)
        return False  # 0x0002?

    # TODO: update coin status
    pass

    return 0x0000

def register(work_id, asset_name):
    wallet_db = IndexedDBWallet()

    my_account = wallet_db.queryAccount(work_id=work_id)

    if my_account == None:
        raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % work_id)

    if wallet_db.findAssetByName(name=asset_name):
        raise RegisterNameError('Transaction Name %s has already existed.'%asset_name)

    part_my = Account(privateKey=my_account['pri_key'])
    wallet = Wallet()

    inputs = []
    outputs = []

    tx = RegisterTransaction(inputs, outputs, AssetType.Token,
                             asset_name, '-0.00000001', part_my.publicKey,
                             part_my.address)

    try:
        txid = wallet.makeTransaction(tx, part_my)
        exit()
    except Exception as e:
        print(e)
        return False  # 0x0002?

    # TODO: update coin status
    pass

    return 0x0000

def issue(work_id, target, asset_name):
    """target format: {work_id: value}"""
    wallet_db = IndexedDBWallet()

    my_account = wallet_db.queryAccount(work_id=work_id)

    if my_account == None:
        raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % work_id)

    if not isinstance(target, dict):
        raise ValueError('Target format should be {work_id: value}.')

    for target_work_id in target.keys():
        target_account = wallet_db.queryAccount(work_id=target_work_id)
        if target_account == None:
            raise WorkIdError('Cannot get the corresponding %s Account in wallet_db.' % target_work_id)

    if not wallet_db.findAssetByName(name=asset_name):
        raise RegisterNameError('Transaction Name %s does not exist.')

    part_my = Account(privateKey=my_account['pri_key'])
    wallet = Wallet()

    inputs = []
    outputs = [TransactionOutput(AssetId=asset_name, Value=str(value),
                                 ScriptHash=wallet_db.queryAccount(work_id=target_work_id).scriptHash)
               for target_work_id, value in target.iteritems]

    tx = IssueTransaction(inputs, outputs)
    try:
        txid = wallet.makeTransaction(tx, part_my)
    except Exception as e:
        print(e)
        return False  # 0x0002?

    # TODO: update coin status
    pass

    return 0x0000

def pay(payer_id, payees, asset):
    wallet_db = IndexedDBWallet()
    # step 1: get payer account
    payer = wallet_db.queryAccount(work_id=payer_id)
    if payer == None:
        print('%s : not exist payer block chain account' % payer_id)
        return 2
1
    payer_acc = Account(payer['pri_key'])
    contract = Contract()
    contract.createSignatureContract(payer_acc.publicKey)

    # step 2: load payer available coins
    coins = wallet_db.loadCoins(address=payer['address'],asset=asset)

    # step 3: select coins
    wallet = Wallet()
    selected_coins = wallet.selectCoins(coins, payees)
    if len(selected_coins) == 0:
        print('no enough coins')
        return 5
    change = sum([int(c.value) for c in selected_coins]) - sum([int(p['amount']) for p in payees])

    # step 4: construct outputs
    outputs = []
    payee_accs = {}
    for p in payees:
        payee = wallet_db.queryAccount(work_id=p['work_id'])
        if payee == None:
            print('%s : not exist payee block chain account' % payer_id)
            return 3
        acc = Account(payee['pri_key'])
        output = TransactionOutput(AssetId=asset, Value=p['amount'], ScriptHash=acc.scriptHash)
        outputs.append(output)
        payee_accs[acc.scriptHash] = acc

    # add change output
    if change > 0:
        outputs.append(TransactionOutput(AssetId=asset,Value=change,ScriptHash=payer_acc.scriptHash))
        payee_accs[payer_acc.scriptHash] = payer_acc

    # step 5: construct inputs
    inputs = [TransactionInput(prevHash=c.txid, prevIndex=c.idx) for c in selected_coins]

    # step 6: make transaction
    tx = Transaction(inputs, outputs)
    stream = MemoryStream()
    writer = BinaryWriter(stream)
    tx.serializeUnsigned(writer)
    reg_tx = stream.toArray()
    txid = tx.ensureHash()
    print('TX ->', repr(reg_tx))
    print('TXID ->',txid)

    # step 7: Signature
    Redeem_script = contract.redeemScript
    sk = SigningKey.from_string(binascii.unhexlify(payer_acc.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
    signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
    regtx = reg_tx + '014140' + signature + '23' + Redeem_script

    # step 8: sendRawTransaction
    node = RemoteNode(url='http://10.84.136.112:20332')
    response = node.sendRawTransaction(regtx)

    # step 9: update coin status
    if response['result'] == True:
        incoming = []
        for i in range(len(outputs)):
            coin = Coin(txid=txid, idx=i, value=outputs[i].Value, asset=asset, address=payee_accs[outputs[i].ScriptHash].address,status=CoinState.Unconfirmed)
            incoming.append(coin)
        wallet_db.onSendTransaction(spending=selected_coins,incoming=incoming)
        return 0
    else:
        return 6

def __test():
    payer = 'test11'
    payees = [{'work_id':'sys','amount':100},{'work_id':'vote_temp','amount':200}]
    asset = 'dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9'
    pay(payer_id=payer, payees=payees, asset=asset)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'test':
            __test()
        elif sys.argv[1] == 'register':
            register(work_id='tangys', asset_name='测试')
        elif sys.argv[1] == 'transfer':
            transfer(work_id='vote_temp', target_work_id='tangys', value='1', remark='cc', asset='dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9')
        else:
            print('error params')
    else:
        print('python UserWallet.py test for __test()')
