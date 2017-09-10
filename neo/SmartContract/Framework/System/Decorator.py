from neo.VM import OpCode

def op_decorate(op):
    def func_wrapper(f):
        return op

    return func_wrapper

def sys_call(call):
    def func_wrapper(f):
        return call

    return func_wrapper
