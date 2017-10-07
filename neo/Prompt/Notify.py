from neo.Core.Blockchain import Blockchain
import json
from neo.UInt160 import UInt160
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

                    tfrom = event_args[0].GetByteArray()
                    tto = event_args[1].GetByteArray()
                    tamount = event_args[2].GetBigInteger()

                    fromaddr = tfrom
                    toaddr = tto
                    try:
                        if len(fromaddr) == 20:
                            fromaddr = Crypto.ToAddress( UInt160(data=tfrom))
                        if len(toaddr) == 20:
                            toaddr = Crypto.ToAddress(UInt160(data=tto))
                    except Exception as e:
                        print("Couldnt convert from/to to address %s " % e)

                    print("[Neo.Runtime.Notify :: Transfer] %s from %s to %s " % (tamount, fromaddr, toaddr))

                elif event_name == 'refund':


                    to = event_args[0].GetByteArray()

                    if len(to) == 20:
                        to = Crypto.ToAddress(UInt160(data=to))

                    print("[Neo.Runtime.Notify :: REFUND] TO %s " % to)
                    amount = event_args[1].GetBigInteger()
                    print("[Neo.Runtime.Notify :: REFUND] amount %s " % amount)

                else:
#                    print("event name not handled %s " % event_args)

                    for arg in event_args:
                        print("[Neo.Runtime.Notify] item %s " % str(arg))

        else:


            interface = state.GetInterface('t')

            if interface is not None:
                hasjson = getattr(interface,'ToJson',None)

                if hasjson:
                    print("[Neo.Runtime.Notify] %s " % json.dumps(interface.ToJson(), indent=4))

                else:
                    print("[Neo.Runtime.Notify] %s " % str(interface))

            else:
                print("[Neo.Runtime.Notify] %s " % str(state))


    except Exception as e:
#        print("could not process notificatiot state %s %s " % (state, e))
        print("[Neo.Runtime.Notify] notify item %s " % str(state))