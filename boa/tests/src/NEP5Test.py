from boa.blockchain.vm.Neo.Action import RegisterAction
from boa.blockchain.vm.Neo.Runtime import GetTrigger,CheckWitness
from boa.blockchain.vm.Neo.TriggerType import Application,Verification

# Token Settings
TOKEN_NAME ='Sample NEP 5'
SYMBOL = 'TKN'

OWNER = bytearray()

DECIMALS=8

FACTOR = 100000000




#ICO SETTINGS
NEO_ASSET_ID = b'\xc5o3\xfcn\xcf\xcd\x0c"\\J\xb3V\xfe\xe5\x93\x90\xaf\x85`\xbe\x0e\x93\x0f\xae\xbet\xa6\xda\xff|\x9b'

# 5million times decimals
TOTAL_AMOUNT = 5000000 * FACTOR

PRE_ICO_CAP = FACTOR

ICO_START_TIME = 1502726400
ICO_END_TIME = 1513936000



#Events

Transfer = RegisterAction('transfer', 'from','to','amount')

Refund = RegisterAction('refund', 'to','amount')


def Main(operation, args):

    trigger = GetTrigger()

    if trigger == Verification():

        owner_len = len(OWNER)

        if owner_len == 20:

            res = CheckWitness(OWNER)
            print("owner verify result %s " % res)
            return res

#        elif owner_len == 33:

#            res = Ver





#    elif trigger == Application():


    return 1


