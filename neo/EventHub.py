#
# This is the central event hub for blockchain and smart contract events,
# which makes it easy for external developers to receive notifications.
#
# Currently (pre-alpha) it works like this:
#
#   from neo.EventHub import events
#
#   @events.on("myevent")
#   def handler1(*args):
#       print("handler1 called with args", args)
#
from neo.Settings import settings
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
# See https://logzero.readthedocs.io/en/latest/#example-usage
from logzero import logger

# pymitter manages the event dispatching (https://github.com/riga/pymitter#examples)
from pymitter import EventEmitter
import json

# `events` is can be imported and used from all parts of the code to dispatch or receive events
events = EventEmitter(wildcard=True)


# Helper for easier dispatching of events from somewhere in the project
def dispatch_smart_contract_event(event_type,
                                  event_payload,
                                  contract_hash,
                                  block_number,
                                  tx_hash,
                                  execution_success=False,
                                  test_mode=False):
    sc_event = SmartContractEvent(event_type, event_payload, contract_hash, block_number, tx_hash, execution_success, test_mode)
    events.emit(event_type, sc_event)


def dispatch_smart_contract_notify(event_type,
                                   event_payload,
                                   contract_hash,
                                   block_number,
                                   tx_hash,
                                   execution_success=False,
                                   test_mode=False):
    notify_event = NotifyEvent(event_type, event_payload, contract_hash, block_number, tx_hash, execution_success, test_mode)
    events.emit(event_type, notify_event)


@events.on("SmartContract.*")
@events.on("SmartContract.*.*")
def on_sc_event(sc_event):
    if not settings.log_smart_contract_events:
        return

    if sc_event.test_mode:
        payload = sc_event.event_payload
        if isinstance(sc_event.event_payload, list):
            payload = []
            for item in sc_event.event_payload:
                if isinstance(item, list):
                    for listitem in item:
                        try:
                            payload.append(json.dumps(listitem.ToJson(), indent=4))
                        except Exception as e:
                            payload.append(listitem)
                else:
                    try:
                        payload.append(json.dumps(item.ToJson(), indent=4))
                    except Exception as e:
                        payload.append(item)
        logger.info("[test_mode][%s] [%s] %s" % (sc_event.event_type, sc_event.contract_hash, payload))
    else:
        payload = sc_event.event_payload
        if isinstance(sc_event.event_payload, list):
            payload = []
            for item in sc_event.event_payload:
                if isinstance(item, list):
                    for listitem in item:
                        try:
                            payload.append(json.dumps(listitem.ToJson(), indent=4))
                        except Exception as e:
                            payload.append(listitem)
                else:
                    try:
                        payload.append(json.dumps(item.ToJson(), indent=4))
                    except Exception as e:
                        payload.append(item)

        logger.info("[%s][%s] [%s] [tx %s] %s" % (sc_event.event_type, sc_event.block_number, sc_event.contract_hash, sc_event.tx_hash.ToString(), payload))
