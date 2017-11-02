

class NotifyEventArgs:

    ScriptContainer = None
    ScriptHash = None
    State = None

    def __init__(self, container, script_hash, state):

        self.ScriptContainer = container
        self.ScriptHash = script_hash
        self.State = state
