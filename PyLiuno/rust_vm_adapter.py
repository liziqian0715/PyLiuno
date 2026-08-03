"""Rust VM 适配器：将 PyLiuno 编译器输出转为 Rust VM 可执行的格式"""
from .bytecode import OpCode

def adapt_instructions(instructions, constants):
    result = []
    for opcode, operand in instructions:
        op_name = opcode.name
        if operand is None:
            result.append((op_name, 0))
        else:
            result.append((op_name, operand))
    return result

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
    adapted = adapt_instructions(instructions, compiler.constants)
    
    vm = RustVM()
    vm.run(adapted, compiler.constants)