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
        
        dispatch = {
            OpCode.LOAD_CONST: self._load_const,
            OpCode.LOAD_NAME: self._load_name,
            OpCode.STORE_NAME: self._store_name,
            OpCode.BINARY_ADD: self._binary_add,
            OpCode.BINARY_SUB: self._binary_sub,
            OpCode.BINARY_MUL: self._binary_mul,
            OpCode.BINARY_DIV: self._binary_div,
            OpCode.BINARY_MOD: self._binary_mod,
            OpCode.BINARY_SUBSCR: self._binary_subscr,
            OpCode.BINARY_IN: self._binary_in,
            OpCode.BINARY_NOT_IN: self._binary_not_in,
            OpCode.BUILD_LIST: self._build_list,
            OpCode.BUILD_DICT: self._build_dict,
            OpCode.COMPARE_EQ: self._compare_eq,
            OpCode.COMPARE_NE: self._compare_ne,
            OpCode.COMPARE_LT: self._compare_lt,
            OpCode.COMPARE_GT: self._compare_gt,
            OpCode.COMPARE_LE: self._compare_le,
            OpCode.COMPARE_GE: self._compare_ge,
            OpCode.PRINT: self._print,
            OpCode.POP_TOP: self._pop_top,
            OpCode.JUMP_IF_FALSE: self._jump_if_false,
            OpCode.JUMP_IF_TRUE: self._jump_if_true,
            OpCode.JUMP_BACKWARD: self._jump_backward,
            OpCode.JUMP_FORWARD: self._jump_forward,
            OpCode.GET_ITER: self._get_iter,
            OpCode.FOR_ITER: self._for_iter,
            OpCode.MAKE_FUNCTION: self._make_function,
            OpCode.CALL_FUNCTION: self._call_function,
            OpCode.RETURN_VALUE: self._return_value,
        }
        
        while self.ip < len(instructions):
            opcode, operand = instructions[self.ip]
            self.ip += 1
            handler = dispatch.get(opcode)
            if handler:
                handler(operand)
            else:
                raise NotImplementedError(f"Unknown opcode: {opcode}")
    
    def _load_const(self, operand):
        self.stack.append(self.constants[operand])
    
    def _load_name(self, operand):
        if operand in self.variables:
            self.stack.append(self.variables[operand])
        else:
            raise NameError(f"name '{operand}' is not defined")
    
    def _store_name(self, operand):
        self.variables[operand] = self.stack.pop()
    
    def _binary_add(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a + b)
    
    def _binary_sub(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)
    
    def _binary_mul(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a * b)
    
    def _binary_div(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a / b)
    
    def _binary_mod(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a % b)
    
    def _binary_subscr(self, operand):
        idx = self.stack.pop()
        obj = self.stack.pop()
        self.stack.append(obj[idx])
    
    def _binary_in(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a in b)
    
    def _binary_not_in(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a not in b)
    
    def _build_list(self, operand):
        items = [self.stack.pop() for _ in range(operand)]
        items.reverse()
        self.stack.append(items)
    
    def _build_dict(self, operand):
        result = {}
        for _ in range(operand):
            v = self.stack.pop()
            k = self.stack.pop()
            result[k] = v
        self.stack.append(result)
    
    def _compare_eq(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a == b)
    
    def _compare_ne(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a != b)
    
    def _compare_lt(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a < b)
    
    def _compare_gt(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a > b)
    
    def _compare_le(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a <= b)
    
    def _compare_ge(self, operand):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >= b)
    
    def _print(self, operand):
        print(self.stack.pop())
    
    def _pop_top(self, operand):
        if self.stack:
            self.stack.pop()
    
    def _jump_if_false(self, operand):
        if not self.stack.pop():
            self.ip = operand
    
    def _jump_if_true(self, operand):
        if self.stack.pop():
            self.ip = operand
    
    def _jump_backward(self, operand):
        self.ip = operand
    
    def _jump_forward(self, operand):
        self.ip = operand
    
    def _get_iter(self, operand):
        obj = self.stack.pop()
        self.stack.append(iter(obj))
    
    def _for_iter(self, operand):
        try:
            val = next(self.stack[-1])
            self.stack.append(val)
        except StopIteration:
            self.stack.pop()
            self.ip = operand
    
    def _make_function(self, operand):
        name, params, body_instrs, body_consts = self.stack.pop()
        self.stack.append(('function', name, params, body_instrs, body_consts))
    
    def _call_function(self, operand):
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
    
    def _return_value(self, operand):
        raise ReturnSignal()