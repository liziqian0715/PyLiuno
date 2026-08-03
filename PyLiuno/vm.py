from .bytecode import OpCode

class ReturnSignal(Exception):
    pass

class VM:
    def __init__(self):
        self.stack = []
        self.variables = {}
        self.constants = []
        self.ip = 0
        
    def run(self, instructions, constants):
        self.constants = constants
        self.ip = 0
        
        while self.ip < len(instructions):
            opcode, operand = instructions[self.ip]
            self.ip += 1
            
            if opcode == OpCode.LOAD_CONST:
                self.stack.append(self.constants[operand])
            elif opcode == OpCode.LOAD_NAME:
                if operand in self.variables:
                    self.stack.append(self.variables[operand])
                else:
                    raise NameError(f"name '{operand}' is not defined")
            elif opcode == OpCode.STORE_NAME:
                self.variables[operand] = self.stack.pop()
            elif opcode == OpCode.BINARY_ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif opcode == OpCode.BINARY_SUB:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif opcode == OpCode.BINARY_MUL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif opcode == OpCode.BINARY_DIV:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a / b)
            elif opcode == OpCode.BINARY_MOD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a % b)
            elif opcode == OpCode.BINARY_SUBSCR:
                idx = self.stack.pop()
                obj = self.stack.pop()
                self.stack.append(obj[idx])
            elif opcode == OpCode.BUILD_LIST:
                items = [self.stack.pop() for _ in range(operand)]
                items.reverse()
                self.stack.append(items)
            elif opcode == OpCode.COMPARE_EQ:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a == b)
            elif opcode == OpCode.COMPARE_NE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a != b)
            elif opcode == OpCode.COMPARE_LT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a < b)
            elif opcode == OpCode.COMPARE_GT:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a > b)
            elif opcode == OpCode.COMPARE_LE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a <= b)
            elif opcode == OpCode.COMPARE_GE:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a >= b)
            elif opcode == OpCode.PRINT:
                print(self.stack.pop())
            elif opcode == OpCode.POP_TOP:
                if self.stack:
                    self.stack.pop()
            elif opcode == OpCode.JUMP_IF_FALSE:
                if not self.stack.pop():
                    self.ip = operand
            elif opcode == OpCode.JUMP_IF_TRUE:
                if self.stack.pop():
                    self.ip = operand
            elif opcode == OpCode.JUMP_BACKWARD:
                self.ip = operand
            elif opcode == OpCode.JUMP_FORWARD:
                self.ip = operand
            elif opcode == OpCode.MAKE_FUNCTION:
                name, params, body_instrs, body_consts = self.stack.pop()
                self.stack.append(('function', name, params, body_instrs, body_consts))
            elif opcode == OpCode.CALL_FUNCTION:
                args = [self.stack.pop() for _ in range(operand)]
                args.reverse()
                func = self.stack.pop()
                if isinstance(func, tuple) and func[0] == 'function':
                    _, name, params, body_instrs, body_consts = func
                    old_vars = self.variables.copy()
                    self.variables.update(zip(params, args))
                    old_ip = self.ip
                    old_stack = self.stack.copy()
                    self.stack = []
                    try:
                        self.run(body_instrs, body_consts)
                    except ReturnSignal:
                        pass
                    result = self.stack[-1] if self.stack else None
                    self.stack = old_stack
                    self.stack.append(result)
                    self.variables = old_vars
                    self.ip = old_ip
                else:
                    raise TypeError(f"'{func}' is not callable")
            elif opcode == OpCode.RETURN_VALUE:
                raise ReturnSignal()
            elif opcode == OpCode.BINARY_IN:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a in b)
            elif opcode == OpCode.BINARY_NOT_IN:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a not in b)
            elif opcode == OpCode.BUILD_DICT:
                result = {}
                for _ in range(operand):
                    v = self.stack.pop()
                    k = self.stack.pop()
                    result[k] = v
                self.stack.append(result)
            elif opcode == OpCode.GET_ITER:
                obj = self.stack.pop()
                self.stack.append(iter(obj))
            elif opcode == OpCode.FOR_ITER:
                try:
                    iterator = self.stack[-1]
                    val = next(iterator)
                    self.stack.append(val)
                except StopIteration:
                    self.stack.pop()  # 弹出迭代器
                    self.ip = operand