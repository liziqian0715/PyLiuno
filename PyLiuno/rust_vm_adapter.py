"""Rust VM 适配器：将 PyLiuno 编译器输出转为 Rust VM 可执行的格式"""
from .bytecode import OpCode

def adapt_instructions(instructions, constants):
    """转换指令和常量，递归处理嵌套函数"""
    result = []
    for opcode, operand in instructions:
        op_name = opcode.name
        if operand is None:
            result.append((op_name, 0))
        else:
            result.append((op_name, operand))
    
    # 递归转换 constants 中的函数体指令
    new_constants = []
    for c in constants:
        if isinstance(c, tuple) and len(c) == 4:
            name, params, body_instrs, body_consts = c
            adapted_body, adapted_body_consts = adapt_instructions(body_instrs, body_consts)
            new_constants.append((name, params, adapted_body, adapted_body_consts))
        else:
            new_constants.append(c)
    return result, new_constants

def run_rust_vm(code: str):
    """用 Rust VM 执行 PyLiuno 代码"""
    from .lexer import tokenize
    from .parser import Parser
    from .compiler import Compiler
    from pyliuno_vm import VM as RustVM
    
    tokens = list(tokenize(code))
    parser = Parser(tokens, source_code=code)
    mod = parser.parse()
    compiler = Compiler()
    instructions = compiler.compile(mod)
    adapted, adapted_consts = adapt_instructions(instructions, compiler.constants)
    
    vm = RustVM()
    vm.run(adapted, adapted_consts)