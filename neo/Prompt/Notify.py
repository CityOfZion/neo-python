from neo.Core.Blockchain import Blockchain



def SubscribeNotifications():

    Blockchain.Default().Notify.on_change += HandleBlockchainNotification

def HandleBlockchainNotification(notification):


    state = notification.State
    try:

        notification_items = state.GetArray()

        if len(notification_items) > 0:
            event_name = notification_items[0].GetString()
            print("event name %s " % event_name)

            event_args = notification_items[1:]


            if event_name == 'transfer':

                tfrom = event_args[0].GetByteArray()
                tto = event_args[1].GetByteArray()
                tamount = event_args[2].GetBigInteger()

                print("Transfer %s from %s to %s " % (tamount, tfrom, tto))

            elif event_name == 'refund':
                to = event_args[0]
                print("REFUND TO %s " % to.GetString())
                amount = event_args[1].GetBigInteger()
                print("refund amount %s " % amount)

            else:
                print("event name not handled %s " % event_args)

                for arg in event_args:
                    print("argument is %s " % str(arg))
    except Exception as e:
        print("could not process notificatiot state %s %s " % (state, e))
        print("notify item %s " % str(state))