import json
import random
import hashlib
import binascii
import requests
from ecdsa import SigningKey, NIST256p


def sendrawtransaction(tx):
    url = "http://101.200.230.134:20332"
    payload = {
        "method": "sendrawtransaction",
        "params": [tx],
        "id": 9,
    }
    try:
        response = requests.post(url, data=json.dumps(payload),  timeout=3).json()
        response = response['result']
    except:
        return 'err'
    return response

def float_2_hex(f):
    base = 0x10000000000000000
    return big_or_little(hex(base + int(f / 0.00000001))[-17:-1])

def big_or_little(string):
    arr = bytearray(string)
    length = len(arr)
    for index in range(length/2):
        if index%2 == 0:
            arr[index], arr[length-2-index] = arr[length-2-index], arr[index]
        else:
            arr[index], arr[length -index] = arr[length -index], arr[index]
    return str(arr)

#第一步先找到所有注册资产
Txid = str(requests.get('http://101.200.230.134:8080/api/v1.0/Register/AW1DTbesc48XszSQkfibkPpufAE5M2B3A1').json()['data'][0]['txid'])

Prikey = ''
Redeem_script = '21030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4bac'
Outputs = [{'scripthash':'fd2596fbd0aa2b5716318ed4a45b7715265357d1',
            'value':1},
           {'scripthash':'2ccab7298ab33df2f920d79940a1f7e820c9c4c9',
            'value':1}]

def Make_IssueTransaction(Prikey, Redeem_script, Outputs, Txid):
    Nonce = random.randint(268435456, 4294967295)
    Nonce = hex(Nonce)[2:-1]
    if len(Nonce)%2==1:
        Nonce = '0'+Nonce
    value = 1
    if len(Outputs)> 16777215 or 'L' in Nonce:
        #未测试,L会出现其中？
        assert False
    IssueTransaction = '01'+ big_or_little(Nonce) + hex(len(Outputs))[2:].zfill(6)
    for o in Outputs:
        IssueTransaction = IssueTransaction + big_or_little(Txid) + float_2_hex(o['value']) + big_or_little(o['scripthash'])
    sk = SigningKey.from_string(binascii.unhexlify(Prikey), curve=NIST256p, hashfunc=hashlib.sha256)
    signature = binascii.hexlify(sk.sign(binascii.unhexlify(IssueTransaction),hashfunc=hashlib.sha256))
    return IssueTransaction + '014140' + signature + '23' + Redeem_script

IT = Make_IssueTransaction(Prikey, Redeem_script, Outputs, Txid)
print sendrawtransaction(IT)
