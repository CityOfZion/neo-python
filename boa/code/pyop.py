
#the following are python opcodes taken from the `opcode` module
#these have been constantized for easier access
#these are the opcodes used by python


#not to be confused with opcodes from neo.VM.OpCode,
#which are the opcodes for the neo vm

POP_TOP = 1
ROT_TWO = 2
ROT_THREE = 3
DUP_TOP = 4
DUP_TOP_TWO = 5

NOP = 9
UNARY_POSITIVE = 10
UNARY_NEGATIVE = 11
UNARY_NOT = 12

UNARY_INVERT = 15

BINARY_MATRIX_MULTIPLY = 16
INPLACE_MATRIX_MULTIPLY = 17

BINARY_POWER = 19
BINARY_MULTIPLY = 20

BINARY_MODULO = 22
BINARY_ADD = 23
BINARY_SUBTRACT = 24
BINARY_SUBSCR = 25
BINARY_FLOOR_DIVIDE = 26
BINARY_TRUE_DIVIDE = 27
INPLACE_FLOOR_DIVIDE = 28
INPLACE_TRUE_DIVIDE = 29

GET_AITER = 50
GET_ANEXT = 51
BEFORE_ASYNC_WITH = 52

INPLACE_ADD = 55
INPLACE_SUBTRACT = 56
INPLACE_MULTIPLY = 57

INPLACE_MODULO = 59
STORE_SUBSCR = 60
DELETE_SUBSCR = 61
BINARY_LSHIFT = 62
BINARY_RSHIFT = 63
BINARY_AND = 64
BINARY_XOR = 65
BINARY_OR = 66
INPLACE_POWER = 67
GET_ITER = 68
GET_YIELD_FROM_ITER = 69

PRINT_EXPR = 70
LOAD_BUILD_CLASS = 71
YIELD_FROM = 72
GET_AWAITABLE = 73

INPLACE_LSHIFT = 75
INPLACE_RSHIFT = 76
INPLACE_AND = 77
INPLACE_XOR = 78
INPLACE_OR = 79
BREAK_LOOP = 80
WITH_CLEANUP_START = 81
WITH_CLEANUP_FINISH = 82

RETURN_VALUE = 83
IMPORT_STAR = 84

YIELD_VALUE = 86
POP_BLOCK = 87
END_FINALLY = 88
POP_EXCEPT = 89


HAVE_ARGUMENT = 90              # Opcodes from here have an argument:

STORE_NAME = 90       # Index in name list
DELETE_NAME = 91      # ""
UNPACK_SEQUENCE = 92   # Number of tuple items

FOR_ITER = 93  #jrel op

UNPACK_EX = 94
STORE_ATTR = 95       # Index in name list
DELETE_ATTR = 96      # ""
STORE_GLOBAL = 97     # ""
DELETE_GLOBAL = 98    # ""
LOAD_CONST = 100       # Index in const list

#hasconst.append(100

LOAD_NAME = 101       # Index in name list
BUILD_TUPLE = 102      # Number of tuple items
BUILD_LIST = 103       # Number of list items
BUILD_SET = 104        # Number of set items
BUILD_MAP = 105        # Number of dict entries (upto 255
LOAD_ATTR = 106       # Index in name list
COMPARE_OP = 107       # Comparison operator

IMPORT_NAME = 108     # Index in name list
IMPORT_FROM = 109     # Index in name list

JUMP_FORWARD = 110    # Number of bytes to skip
JUMP_IF_FALSE_OR_POP = 111 # Target byte offset from beginning of code
JUMP_IF_TRUE_OR_POP = 112  # "jabs op"
JUMP_ABSOLUTE = 113        # "jabs op"
POP_JUMP_IF_FALSE = 114    # "jabs op"
POP_JUMP_IF_TRUE = 115     # "jabs op"

LOAD_GLOBAL = 116     # Index in name list

CONTINUE_LOOP = 119   # Target address jrel
SETUP_LOOP = 120      # Distance to target address jrel
SETUP_EXCEPT = 121    # "jrel"
SETUP_FINALLY = 122   # "jrel"

LOAD_FAST = 124        # Local variable number
STORE_FAST = 125       # Local variable number
DELETE_FAST = 126      # Local variable number

RAISE_VARARGS = 130    # Number of raise arguments (1, 2, or 3
CALL_FUNCTION = 131    # #args + (#kwargs << 8


MAKE_FUNCTION = 132    # Number of args with default values
BUILD_SLICE = 133      # Number of items
MAKE_CLOSURE = 134
LOAD_CLOSURE = 135

LOAD_DEREF = 136

STORE_DEREF = 137

DELETE_DEREF = 138

CALL_FUNCTION_VAR = 140     # #args + (#kwargs << 8
CALL_FUNCTION_KW = 141      # #args + (#kwargs << 8
CALL_FUNCTION_VAR_KW = 142  # #args + (#kwargs << 8

SETUP_WITH = 143

LIST_APPEND = 145
SET_ADD = 146
MAP_ADD = 147

LOAD_CLASSDEREF = 148

SETUP_ASYNC_WITH = 154

EXTENDED_ARG = 144

BUILD_LIST_UNPACK = 149
BUILD_MAP_UNPACK = 150
BUILD_MAP_UNPACK_WITH_CALL = 151
BUILD_TUPLE_UNPACK = 152
BUILD_SET_UNPACK = 153


#boa custom ops

FROMALTSTACK = 241
DROP = 242