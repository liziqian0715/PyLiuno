from .bytecode import OpCode
from . import ast as ast_nodes

class Compiler:
    def __init__(self):
        self.instructions = []
        self.constants = []
        
    def emit(self, opcode, operand=None):
        self.instructions.append((opcode, operand))
        
    def compile(self, node):
        t = type(node).__name__
        
        if t == 'Module':
            for stmt in node.body:
                self.compile(stmt)
                
        elif t == 'ExprStmt':
            self.compile(node.expr)
            self.emit(OpCode.POP_TOP)
            
        elif t == 'Number':
            self.constants.append(node.value)
            self.emit(OpCode.LOAD_CONST, len(self.constants) - 1)
            
        elif t == 'String':
            self.constants.append(node.value)
            self.emit(OpCode.LOAD_CONST, len(self.constants) - 1)
            
        elif t == 'Name':
            self.emit(OpCode.LOAD_NAME, node.id)
            
        elif t == 'ListNode':
            for elem in node.elements:
                self.compile(elem)
            self.emit(OpCode.BUILD_LIST, len(node.elements))
            
        elif t == 'Subscript':
            self.compile(node.value)
            self.compile(node.index)
            self.emit(OpCode.BINARY_SUBSCR)
            
        elif t == 'BinaryOp':
            self.compile(node.left)
            self.compile(node.right)
            op_map = {
                '+': OpCode.BINARY_ADD, '-': OpCode.BINARY_SUB,
                '*': OpCode.BINARY_MUL, '/': OpCode.BINARY_DIV,
                '%': OpCode.BINARY_MOD,
                '==': OpCode.COMPARE_EQ, '!=': OpCode.COMPARE_NE,
                '<': OpCode.COMPARE_LT, '>': OpCode.COMPARE_GT,
                '<=': OpCode.COMPARE_LE, '>=': OpCode.COMPARE_GE,
                'in': OpCode.BINARY_IN,
                'not_in': OpCode.BINARY_NOT_IN,
            }
            if node.op in op_map:
                self.emit(op_map[node.op])
                
        elif t == 'Assign':
            self.compile(node.value)
            self.emit(OpCode.STORE_NAME, node.target.id)
            
        elif t == 'Print':
            for arg in node.args:
                self.compile(arg)
                self.emit(OpCode.PRINT)
                
        elif t == 'If':
            self.compile(node.test)
            jump_idx = len(self.instructions)
            self.emit(OpCode.JUMP_IF_FALSE, None)
            for s in node.body:
                self.compile(s)
            end_idx = len(self.instructions)
            self.instructions[jump_idx] = (OpCode.JUMP_IF_FALSE, end_idx)
            
        elif t == 'While':
            start_idx = len(self.instructions)
            self.compile(node.test)
            jump_idx = len(self.instructions)
            self.emit(OpCode.JUMP_IF_FALSE, None)
            for s in node.body:
                self.compile(s)
            self.emit(OpCode.JUMP_BACKWARD, start_idx)
            end_idx = len(self.instructions)
            self.instructions[jump_idx] = (OpCode.JUMP_IF_FALSE, end_idx)
            
        elif t == 'FuncDef':
            func_compiler = Compiler()
            func_compiler.compile_body(node.body)
            self.constants.append((node.name, node.params, func_compiler.instructions, func_compiler.constants))
            idx = len(self.constants) - 1
            self.emit(OpCode.LOAD_CONST, idx)
            self.emit(OpCode.MAKE_FUNCTION)
            self.emit(OpCode.STORE_NAME, node.name)
            
        elif t == 'Call':
            self.compile(node.func)
            for arg in node.args:
                self.compile(arg)
            self.emit(OpCode.CALL_FUNCTION, len(node.args))
            
        elif t == 'Return':
            if node.value:
                self.compile(node.value)
            else:
                self.constants.append(None)
                self.emit(OpCode.LOAD_CONST, len(self.constants) - 1)
            self.emit(OpCode.RETURN_VALUE)
        elif t == 'DictNode':
            for key_node, val_node in node.pairs:
                self.compile(key_node)
                self.compile(val_node)
            self.emit(OpCode.BUILD_DICT, len(node.pairs))
        elif t == 'For':
            self.compile(node.iter)
            self.emit(OpCode.GET_ITER)
            start_idx = len(self.instructions)
            # FOR_ITER 从迭代器取下一个值，如果耗尽则跳转
            self.emit(OpCode.FOR_ITER, None)
            # 栈顶现在是下一个值，存到循环变量
            # 注意：FOR_ITER 已经把值放栈上了
            self.emit(OpCode.STORE_NAME, node.target.id)
            for s in node.body:
                self.compile(s)
            self.emit(OpCode.JUMP_BACKWARD, start_idx)
            end_idx = len(self.instructions)
            self.instructions[start_idx] = (OpCode.FOR_ITER, end_idx)
            # 循环结束后弹出迭代器
            self.emit(OpCode.POP_TOP)
            
        return self.instructions
        
    def compile_body(self, body):
        for stmt in body:
            self.compile(stmt)
        return self.instructions