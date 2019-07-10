class LogEventArgs:
    def __init__(self, container, script_hash, message):
        self.ScriptContainer = container
        self.ScriptHash = script_hash
        self.Message = message
