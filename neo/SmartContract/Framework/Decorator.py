from neo.VM import OpCode


def op_decorate(op):
    def func_wrapper():
        return op
        
    return func_wrapper


def sys_call(call):
    def func_wrapper():
        return call

    return func_wrapper