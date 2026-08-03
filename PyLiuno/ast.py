"""AST node definitions for PyLiuno"""
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

class Node:
    pass

@dataclass
class Module(Node):
    body: List[Node]

@dataclass
class ExprStmt(Node):
    expr: Node

@dataclass
class Assign(Node):
    target: 'Name'
    value: Node

@dataclass
class Return(Node):
    value: Optional[Node]

@dataclass
class Print(Node):
    args: List[Node]

@dataclass
class If(Node):
    test: Node
    body: List[Node]
    orelse: Optional[List[Node]]

@dataclass
class While(Node):
    test: Node
    body: List[Node]

@dataclass
class FuncDef(Node):
    name: str
    params: List[str]
    body: List[Node]
    # defaults: mapping param name -> AST node for default expression (optional)
    defaults: Optional[Dict[str, Any]] = None

# Expressions
@dataclass
class Name(Node):
    id: str

@dataclass
class Number(Node):
    value: Any

@dataclass
class String(Node):
    value: str

@dataclass
class Call:
    func: Any
    args: List[Any]
    kwargs: Dict[str, Any] = None

@dataclass
class ListNode(Node):
    elements: List[Node]

@dataclass
class Subscript(Node):
    value: Node
    index: Node

@dataclass
class DictNode(Node):
    # elements as list of (key_node, value_node)
    pairs: List[Any]

@dataclass
class For(Node):
    target: 'Name'
    iter: Node
    body: List[Node]

@dataclass
class Break(Node):
    pass

@dataclass
class Continue(Node):
    pass

@dataclass
class BinaryOp(Node):
    left: Node
    op: str
    right: Node

@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

@dataclass
class Global:
    names: List[str]

@dataclass
class MethodCall:
    obj: Any
    method: str
    args: List[Any]

@dataclass
class Import:
    filename: str

# Simple pretty printer for AST
def dump(node, indent=0):
    pad = '  ' * indent
    if isinstance(node, Module):
        s = pad + 'Module\n'
        for n in node.body:
            s += dump(n, indent+1)
        return s
    typ = type(node).__name__
    fields = getattr(node, '__dataclass_fields__', {})
    if not fields:
        return pad + f'{typ}: {node}\n'
    s = pad + typ + '\n'
    for f in fields:
        v = getattr(node, f)
        if isinstance(v, list):
            s += pad + '  ' + f + ':\n'
            for item in v:
                s += dump(item, indent+2)
        elif isinstance(v, Node):
            s += pad + '  ' + f + ':\n' + dump(v, indent+2)
        else:
            s += pad + '  ' + f + ': ' + repr(v) + '\n'
    return s
