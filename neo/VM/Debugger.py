import datetime
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM import VMState
from neo.Settings import settings
from neo.Prompt.vm_debugger import VMDebugger
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class Debugger:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine
        self.engine.debugger = self
        self._breakpoints = dict()

    def Execute(self):
        self.engine._VMState &= ~VMState.BREAK

        def loop_execute_next():
            while self.engine._VMState & VMState.HALT == 0 \
                    and self.engine._VMState & VMState.FAULT == 0 \
                    and self.engine._VMState & VMState.BREAK == 0:
                self.ExecuteAndCheckBreakpoint()

        if settings.log_vm_instructions:
            with open(self.engine.log_file_name, 'w') as self.log_file:
                self.engine.write_log(str(datetime.datetime.now()))
                loop_execute_next()
        else:
            loop_execute_next()

        return not self.engine._VMState & VMState.FAULT > 0

    def ExecuteAndCheckBreakpoint(self):
        self.engine.ExecuteNext()

        if self.engine._VMState == VMState.NONE and self.engine._InvocationStack.Count > 0:
            script_hash = self.engine.CurrentContext.ScriptHash()
            bps = self._breakpoints.get(script_hash, None)
            if bps is not None:
                if self.engine.CurrentContext.InstructionPointer in bps:
                    self.engine._VMState = VMState.BREAK
                    self.engine._vm_debugger = VMDebugger(self.engine)
                    self.engine._vm_debugger.start()

    def AddBreakPoint(self, script_hash, position):
        ctx_breakpoints = self._breakpoints.get(script_hash, None)
        if ctx_breakpoints is None:
            self._breakpoints[script_hash] = set([position])
        else:
            # add by reference
            ctx_breakpoints.add(position)

    def RemoveBreakPoint(self, script_hash, position):
        # test if any breakpoints exist for script hash
        ctx = self._breakpoints.get(script_hash, None)
        if ctx is None:
            return False

        # remove if specific bp exists
        if position in ctx:
            ctx.remove(position)
        else:
            return False

        # clear set from breakpoints list if no more bp's exist for it
        if len(ctx) == 0:
            del self._breakpoints[script_hash]

        return True

    def StepInto(self):

        if self.engine._VMState & VMState.HALT > 0 or self.engine._VMState & VMState.FAULT > 0:
            logger.debug("stopping because vm state is %s " % self.engine._VMState)
            return
        self.engine.ExecuteNext()
        if self.engine._VMState == VMState.NONE:
            self.engine._VMState = VMState.BREAK

    def StepOut(self):
        self.engine._VMState &= ~VMState.BREAK
        c = self.engine.InvocationStack.Count

        while self.engine._VMState & VMState.HALT == 0 \
                and self.engine._VMState & VMState.FAULT == 0 \
                and self.engine._VMState & VMState.BREAK == 0 \
                and self.engine.InvocationStack.Count >= c:
            self.ExecuteAndCheckBreakpoint()

        if self.engine._VMState == VMState.NONE:
            self.engine._VMState = VMState.BREAK

    def StepOver(self):
        if self.engine._VMState & VMState.HALT > 0 or self.engine._VMState & VMState.FAULT > 0:
            return

        self.engine._VMState &= ~VMState.BREAK
        c = self.engine.InvocationStack.Count
        while True:
            self.ExecuteAndCheckBreakpoint()

            go_on = self.engine._VMState & VMState.HALT == 0 \
                    and self.engine._VMState & VMState.FAULT == 0 \
                    and self.engine._VMState & VMState.BREAK == 0 \
                    and self.engine.InvocationStack.Count > c  # noqa
            if not go_on:
                break

        if self.engine._VMState == VMState.NONE:
            self.engine._VMState = VMState.BREAK
