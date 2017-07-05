from bitcoin import *
import binascii
import requests
from ecdsa import SigningKey, NIST256p
import hashlib
import random
from AntShares.Helper import big_or_little_str
from AntShares.Defaults import TEST_NODE

#030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4b
pubkey = privkey_to_pubkey('7d989d02dff495cc1bbc35e891c153b98781e015a20ce276b86afc7856f85efa')
pubkey = '21'+ pubkey
pubkey = binascii.unhexlify(pubkey)
RedeemScript = pubkey + from_int_to_byte(int('ac',16))
#print binascii.hexlify(RedeemScript)
#script_hash_ = binascii.hexlify(bin_hash160(RedeemScript))
#print script_hash_
script_hash_ = big_or_little_str('e63468c1384b94a76bf694f9a1816cc94f7c4b6f')
print bin_to_b58check(binascii.unhexlify(script_hash_),int('17',16))


def sendrawtransaction(tx):
    url = TEST_NODE
    payload = {
        "method": "sendrawtransaction",
        "params": [tx],
        "id": 9,
    }
    try:
        response = requests.post(url, data=json.dumps(payload),  timeout=3).json()
        response = response['result']
    except Exception as e:
        print e
        return 'err'
    return response

def float_2_hex(f):
    base = 0x10000000000000000
    return big_or_little_str(hex(base + int(f / 0.00000001))[-17:-1])

def name_to_hex(name):
    tmp = ''
    for x in name:
        tmp += hex(ord(x))[2:]
    return tmp
'''
#第一步先找到所有inputs
inputs = requests.get('http://101.200.230.134:8080/api/v1.0/getinfo_with_address/AW1DTbesc48XszSQkfibkPpufAE5M2B3A1').json()['data']
#先简单找个较优inputs,之后再优化
inputs = sorted(inputs.iteritems(), key=lambda x:x[1]['value'], reverse=False)
if len(inputs)>1:
    for i in inputs:
        if type(i[0][1]['value']) < 100:
            continue
        txid,count = i[0][0], float(i[0][1]['value'])
else:
    txid,count = inputs[0][0], float(inputs[0][1]['value'])
#print txid, count
Name = '测试'
Issuer = '030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4b'
Admin = '9c17b4ee1441676e36d77a141dd77869d271381d'
Inputs = txid.split('-')[0]
Index = txid.split('-')[1]
Count = count
Prikey = '7d989d02dff495cc1bbc35e891c153b98781e015a20ce276b86afc7856f85efa'
Redeem_script = '21030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4bac'
'''

#第一步先找到所有注册资产
Txid = str(requests.get('http://101.200.230.134:8080/api/v1.0/Register/AW1DTbesc48XszSQkfibkPpufAE5M2B3A1').json()['data'][0]['txid'])

Prikey = '7d989d02dff495cc1bbc35e891c153b98781e015a20ce276b86afc7856f85efa'
Redeem_script = '21030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4bac'
Outputs = [{'scripthash':'fd2596fbd0aa2b5716318ed4a45b7715265357d1',
            'value':1},
           {'scripthash':'2ccab7298ab33df2f920d79940a1f7e820c9c4c9',
            'value':1}]
#http://101.200.230.134:8080/api/v1.0/Register/AW1DTbesc48XszSQkfibkPpufAE5M2B3A1

def Make_IssueTransaction(Prikey, Redeem_script, Outputs, Txid):
    Nonce = random.randint(268435456, 4294967295)
    Nonce = hex(Nonce)[2:-1]
    if len(Nonce)%2==1:
        Nonce = '0'+Nonce
    value = 1
    if len(Outputs)> 16777215 or 'L' in Nonce:
        #未测试,L会出现其中？
        assert False
    IssueTransaction = '01'+ big_or_little_str(Nonce) + hex(len(Outputs))[2:].zfill(6)
    for o in Outputs:
        IssueTransaction = IssueTransaction + big_or_little_str(Txid) + float_2_hex(o['value']) + big_or_little_str(o['scripthash'])
    sk = SigningKey.from_string(binascii.unhexlify(Prikey), curve=NIST256p, hashfunc=hashlib.sha256)
    signature = binascii.hexlify(sk.sign(binascii.unhexlify(IssueTransaction),hashfunc=hashlib.sha256))
    return IssueTransaction + '014140' + signature + '23' + Redeem_script

IT = Make_IssueTransaction(Prikey, Redeem_script, Outputs, Txid)
print sendrawtransaction(IT)

def Make_RegisterTransaction(Prikey, Redeem_script, Name, Issuer, Admin, Inputs, Index, Count, Amount=-0.00000001):
    '''
    Name:发行的资产名
    Issuer:发行者
    Admin:管理员
    Inputs
    Count:inputs
    Amount:发行资产总量，默认无上限-0.00000001
    '''
    Name = '5b7b276c616e67273a277a682d434e272c276e616d65273a27{0}277d5d'.format(name_to_hex(Name))
    Amount = float_2_hex(Amount)
    #不需要找零
    #Antcoin:f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b
    Outputs = big_or_little_str('f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b') + float_2_hex(Count-100) + Admin if Count > 100 else ''
    #暂时支持1个inputs之后再改,'00'为索引
    RegisterTransaction = '4060' + hex(len(Name)/2)[2:] + Name + Amount + Issuer + Admin + '0001' + big_or_little_str(str(Inputs)) + '00'
    if Count > 100:
        RegisterTransaction += '0001' + Outputs
    else:
        RegisterTransaction += '0000'
    GetHashForSigning = big_or_little_str(sha256(binascii.unhexlify(RegisterTransaction)))#txid
    #print GetHashForSigning
    sk = SigningKey.from_string(binascii.unhexlify(Prikey), curve=NIST256p, hashfunc=hashlib.sha256)
    signature = binascii.hexlify(sk.sign(binascii.unhexlify(RegisterTransaction),hashfunc=hashlib.sha256))   
    return RegisterTransaction + '014140' + signature + '23' + Redeem_script

#RT = Make_RegisterTransaction(Prikey, Redeem_script, Name, Issuer, Admin, Inputs, Index, Count)
#print sendrawtransaction(RT)


#scripthash = '1d3871d26978d71d147ad7366e674114eeb4179c'
