from neo.Core.Blockchain import Blockchain
import json
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256
from neo.Cryptography.Crypto import Crypto


def SubscribeNotifications():

    Blockchain.Default().Notify.on_change += HandleBlockchainNotification


def HandleBlockchainNotification(notification):

    state = notification.State
    try:

        if state.IsArray:
            notification_items = state.GetArray()

            if len(notification_items) > 0:
                event_name = notification_items[0].GetString()
                print("[Neo.Runtime.Notify] event name -> %s " % event_name)

                event_args = notification_items[1:]

                if event_name == 'transfer':

                    notify_transfer(event_args)

                elif event_name == 'refund':

                    notify_refund(event_args)

                elif event_name == 'withdrawApproved':

                    notify_withdraw_approved(event_args)

                elif event_name in ['deposit', 'withdraw', 'withdraw_reconcile']:

                    notify_other(event_name, event_args)

                else:
                    #                    print("event name not handled %s " % event_args)

                    for arg in event_args:
                        print("[Neo.Runtime.Notify] item %s " % str(arg))

        else:

            interface = state.GetInterface()

            if interface is not None:
                hasjson = getattr(interface, 'ToJson', None)

                if hasjson:
                    print("[Neo.Runtime.Notify] %s " % json.dumps(interface.ToJson(), indent=4))

                else:
                    print("[Neo.Runtime.Notify] %s " % str(interface))

            else:
                output = {'string': str(state), 'integer': state.GetBigInteger()}
                print("[Neo.Runtime.Notify] %s" % json.dumps(output, indent=4))

    except Exception as e:
        #        print("could not process notificatiot state %s %s " % (state, e))
        print("[Neo.Runtime.Notify] notify item %s " % str(state))


def notify_transfer(event_args):

    tfrom = event_args[0].GetByteArray()
    tto = event_args[1].GetByteArray()
    tamount = event_args[2].GetBigInteger()

    fromaddr = tfrom
    toaddr = tto
    try:
        if len(fromaddr) == 20:
            fromaddr = Crypto.ToAddress(UInt160(data=tfrom))
        if len(toaddr) == 20:
            toaddr = Crypto.ToAddress(UInt160(data=tto))
    except Exception as e:
        print("Couldnt convert from/to to address %s " % e)

    print("[Neo.Runtime.Notify :: Transfer] %s from %s to %s " % (tamount, fromaddr, toaddr))


def notify_refund(event_args):
    to = event_args[0].GetByteArray()

    if len(to) == 20:
        to = Crypto.ToAddress(UInt160(data=to))

    print("[Neo.Runtime.Notify :: REFUND] TO %s " % to)
    amount = event_args[1].GetBigInteger()
    print("[Neo.Runtime.Notify :: REFUND] amount %s " % amount)


def notify_other(event_name, event_args):
    to = event_args[0].GetByteArray()

    if len(to) == 20:
        to = Crypto.ToAddress(UInt160(data=to))

    ename = event_name.upper()
    print("[Neo.Runtime.Notify :: %s] TO %s " % (ename, to))
    amount = event_args[1].GetBigInteger()
    print("[Neo.Runtime.Notify :: %s] amount %s " % (ename, amount))


def notify_withdraw_approved(event_args):

    try:
        to = event_args[0].GetByteArray()
        if len(to) == 20:
            to = Crypto.ToAddress(UInt160(data=to))

        res = {
            'event': 'Withdraw Request Approved',
            'to': to
        }

        vin_requests = event_args[1]

        output = []
        for item in vin_requests.GetArray():
            vin = item.GetArray()
            txid = UInt256(data=vin[0].GetByteArray())
            index = vin[1].GetBigInteger()
            output.append({'txid': txid.ToString(), 'index': index})

        res['vins'] = output

        print("[Neo.Runtime.Notify] %s " % json.dumps(res, indent=4))
    except Exception as e:
        print("couldnt do witdraw approved? %s " % e)
