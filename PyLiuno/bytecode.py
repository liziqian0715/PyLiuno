"""PyLiuno 字节码指令集"""
from enum import Enum, auto

class OpCode(Enum):
    LOAD_CONST = auto()
    LOAD_NAME = auto()
    STORE_NAME = auto()
    LOAD_GLOBAL = auto()
    
    BINARY_ADD = auto()
    BINARY_SUB = auto()
    BINARY_MUL = auto()
    BINARY_DIV = auto()
    BINARY_MOD = auto()
    BINARY_SUBSCR = auto()
    
    BUILD_LIST = auto()
    
    COMPARE_EQ = auto()
    COMPARE_NE = auto()
    COMPARE_LT = auto()
    COMPARE_GT = auto()
    COMPARE_LE = auto()
    COMPARE_GE = auto()
    
    JUMP_FORWARD = auto()
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()
    JUMP_BACKWARD = auto()
    
    MAKE_FUNCTION = auto()
    CALL_FUNCTION = auto()
    RETURN_VALUE = auto()
    
    PRINT = auto()
    POP_TOP = auto()
    SETUP_LOOP = auto()
    POP_BLOCK = auto()
    BREAK_LOOP = auto()

    BINARY_IN = auto()
    BINARY_NOT_IN = auto()
    BUILD_DICT = auto()
    GET_ITER = auto()
    FOR_ITER = auto()