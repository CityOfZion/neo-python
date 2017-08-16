from neo.VM.InteropService import InteropService

import events

class StateReader(InteropService):


    Notify = events.Events()
    Log = events.Events()

    __Instance = None


    @staticmethod
    def Instance():
        if StateReader.__Instance is None:
            StateReader.__Instance = StateReader()
        return StateReader.__Instance

    def __init__(self):

        #register bunch of things
        pass


