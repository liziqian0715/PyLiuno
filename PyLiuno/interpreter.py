"""Interpreter for PyLiuno AST"""
from dataclasses import dataclass
from typing import Any, Dict, List
from . import ast as ast_nodes
from .lexer import Token
from . import settings
import json
import os
import sys

# load i18n resource
_i18n_path = os.path.join(os.path.dirname(__file__), 'i18n.json')
try:
    with open(_i18n_path, 'r', encoding='utf-8') as _f:
        _I18N = json.load(_f)
except Exception:
    _I18N = {'en': {}}

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class LocalizedKeyError(KeyError):
    def __str__(self):
        return self.args[0] if self.args else ''

@dataclass
class Function:
    name: str
    params: List[str]
    body: List[Any]
    closure: Dict[str, Any]
    defaults: Dict[str, Any] = None

    def call(self, interpreter, args):
        # Validate argument counts (positional only for now)
        if len(args) > len(self.params):
            if settings.LANGUAGE == 'zh':
                raise TypeError(f"类型错误: {self.name}() 接受 {len(self.params)} 个位置参数，但给定了 {len(args)} 个")
            raise TypeError(f"{self.name}() takes {len(self.params)} positional arguments but {len(args)} were given")
        # count required params
        num_required = sum(1 for p in self.params if not (self.defaults and p in self.defaults))
        if len(args) < num_required:
            if settings.LANGUAGE == 'zh':
                raise TypeError(f"类型错误: {self.name}() 缺少必需的位置参数")
            raise TypeError(f"{self.name}() missing required positional arguments")

        # Prepare local environment
        local = {}
        # assign provided positional args
        for p, a in zip(self.params, args):
            local[p] = a
        # fill defaults for remaining params
        for p in self.params[len(args):]:
            if self.defaults and p in self.defaults:
                local[p] = self.defaults[p]
            else:
                if settings.LANGUAGE == 'zh':
                    raise TypeError(f"类型错误: {self.name}() 缺少必需的位置参数 '{p}'")
                raise TypeError(f"{self.name}() missing required positional argument '{p}'")

        # push frame and execute
        interpreter.push_frame(local)
        try:
            for stmt in self.body:
                try:
                    interpreter.exec_stmt(stmt)
                except (ReturnSignal, BreakSignal, ContinueSignal):
                    # propagate control signals without annotating
                    raise
                except Exception as e:
                    # annotate/localize runtime error with statement lineno if available
                    lineno = getattr(stmt, 'lineno', None)
                    if lineno is None:
                        if hasattr(stmt, 'expr') and getattr(stmt.expr, 'lineno', None) is not None:
                            lineno = stmt.expr.lineno
                        elif hasattr(stmt, 'args') and stmt.args:
                            for arg in stmt.args:
                                if getattr(arg, 'lineno', None) is not None:
                                    lineno = arg.lineno
                                    break
                        elif hasattr(stmt, 'value') and getattr(stmt.value, 'lineno', None) is not None:
                            lineno = stmt.value.lineno
                    new_exc = interpreter._localize_exception(e, lineno)
                    if new_exc is e:
                        raise
                    raise new_exc from e
        except ReturnSignal as rs:
            interpreter.pop_frame()
            return rs.value
        interpreter.pop_frame()
        return None

class Interpreter:
    def __init__(self, source_code: str = None):
        self.frames: List[Dict[str, Any]] = [{}]
        self.source_code = source_code  # 保存源代码，用于错误时显示 ^ 指向
        self.frames[0]['print'] = self.builtin_print
        # add built-in literals and functions
        self.frames[0]['True'] = True
        self.frames[0]['False'] = False
        self.frames[0]['None'] = None
        # add built-in range(), len(), enumerate(), str/int/float/bool/list
        self.frames[0]['range'] = self.builtin_range
        self.frames[0]['len'] = self.builtin_len
        self.frames[0]['enumerate'] = self.builtin_enumerate
        self.frames[0]['str'] = self.builtin_str
        self.frames[0]['int'] = self.builtin_int
        self.frames[0]['float'] = self.builtin_float
        self.frames[0]['bool'] = self.builtin_bool
        self.frames[0]['list'] = self.builtin_list
        self.frames[0]['__globals__'] = set()
        self.frames[0]['open'] = self.builtin_open
        self.frames[0]['read'] = self.builtin_read
        self.frames[0]['write'] = self.builtin_write
        self.frames[0]['sort'] = self.builtin_sort
        self.frames[0]['sum'] = self.builtin_sum
        self.frames[0]['max'] = self.builtin_max
        self.frames[0]['min'] = self.builtin_min
        self.frames[0]['type'] = self.builtin_type
        self.frames[0]['input'] = self.builtin_input


    def builtin_range(self, *args):
        # support range(stop), range(start, stop), range(start, stop, step)
        if len(args) == 1:
            stop = args[0]
            return range(stop)
        if len(args) == 2:
            start, stop = args
            return range(start, stop)
        if len(args) == 3:
            start, stop, step = args
            return range(start, stop, step)
        raise TypeError(f'range expected at most 3 arguments, got {len(args)}')

    def builtin_len(self, obj):
        try:
            return len(obj)
        except Exception:
            raise TypeError(f"object of type '{type(obj).__name__}' has no len()")

    def builtin_enumerate(self, iterable, start=0):
        # return a Python enumerate object; interpreter's for-loop can iterate over it
        try:
            return enumerate(iterable, start)
        except Exception:
            raise TypeError('enumerate() expects an iterable and an optional start integer')

    def builtin_str(self, obj=None):
        try:
            return str(obj)
        except Exception:
            raise TypeError('str() argument must be convertible to string')

    def builtin_int(self, obj=0):
        try:
            return int(obj)
        except Exception as e:
            raise TypeError(f'int() argument must be convertible to int: {e}')

    def builtin_float(self, obj=0.0):
        try:
            return float(obj)
        except Exception as e:
            raise TypeError(f'float() argument must be convertible to float: {e}')

    def builtin_bool(self, obj=False):
        try:
            return bool(obj)
        except Exception as e:
            raise TypeError(f'bool() argument error: {e}')

    def builtin_list(self, iterable=None):
        try:
            if iterable is None:
                return []
            return list(iterable)
        except Exception as e:
            if settings.LANGUAGE == 'zh':
                raise TypeError(f"类型错误: list() 的参数必须是可迭代的: {e}")
            raise TypeError(f'list() argument must be iterable: {e}')

    def builtin_open(self, filename, mode='r'):
        try:
            return open(filename, mode)
        except Exception as e:
            raise IOError(f"无法打开文件 '{filename}': {e}")

    def builtin_read(self, file):
        try:
            return file.read()
        except Exception as e:
            raise IOError(f"读取文件失败: {e}")

    def builtin_write(self, file, content):
        try:
            return file.write(str(content))
        except Exception as e:
            raise IOError(f"写入文件失败: {e}")

    def _match_error(self, e, error_type):
        mapping = {
            '除零错误': 'ZeroDivisionError',
            'ZeroDivisionError': 'ZeroDivisionError',
            '名称错误': 'NameError',
            'NameError': 'NameError',
            '类型错误': 'TypeError',
            'TypeError': 'TypeError',
            '索引错误': 'IndexError',
            'IndexError': 'IndexError',
            '键错误': 'KeyError',
            'KeyError': 'KeyError',
            '值错误': 'ValueError',
            'ValueError': 'ValueError',
            '语法错误': 'SyntaxError',
            'SyntaxError': 'SyntaxError',
            '所有错误': 'Exception',
        }
        cls_name = mapping.get(error_type)
        if cls_name:
            cls = {'ZeroDivisionError': ZeroDivisionError, 'NameError': NameError,
                   'TypeError': TypeError, 'IndexError': IndexError, 'KeyError': KeyError,
                   'ValueError': ValueError, 'SyntaxError': SyntaxError,
                   'Exception': Exception}.get(cls_name)
            return cls and isinstance(e, cls)
        return False

    def _localize_exception(self, e: Exception, lineno: int = None):
        base_msg = str(e)
        lang = settings.LANGUAGE if hasattr(settings, 'LANGUAGE') else 'en'
        already_localized = getattr(e, 'localized', False) or (
            lang == 'zh' and base_msg.startswith('运行时错误')) or (
            lang != 'zh' and base_msg.startswith('RuntimeError'))
        original_col = getattr(e, 'col', 0)  # 在开头保存原始异常的列号
        loc = f" (line {lineno})" if lineno is not None else ""
        templates = _I18N.get(lang, _I18N.get('en', {}))

        def _add_source_line_to_message(msg):
            if lineno is None or not hasattr(self, 'source_code') or not self.source_code:
                return msg
            if '\n' in msg:
                return msg
            lines = self.source_code.split('\n')
            if lineno - 1 >= len(lines):
                return msg
            src_line = lines[lineno - 1].replace('\t', '    ')
            col = original_col
            if col <= 0:
                cause = getattr(e, '__cause__', None)
                if cause:
                    col = getattr(cause, 'col', 0)
            if col > 0 and col <= len(src_line) + 1:
                token_len = getattr(e, 'token_len', None)
                if token_len is None:
                    import re
                    name_match = re.search(r"'([^']*)'", base_msg)
                    token_len = len(name_match.group(1)) if name_match else 1
                pointer = ' ' * (col - 1) + '^' * token_len
                displayed_line = src_line.rstrip()
                return f"{msg}{loc}\n    {displayed_line}\n    {pointer}"
            displayed_line = src_line.rstrip()
            return f"{msg}{loc}\n    {displayed_line}"

        if already_localized:
            new_msg = _add_source_line_to_message(base_msg)
            if new_msg != base_msg:
                e.args = (new_msg,)
                e.localized = True
                if lineno is not None:
                    e.lineno = lineno
            return e

        def fmt(key, detail=base_msg):
            tpl = templates.get(key)
            if not tpl:
                return detail  # 不加 loc
            return tpl.format(detail=detail, loc='')  # 不加 loc

        def strip_prefix(detail, prefix_en, prefix_zh):
            if lang == 'zh' and detail.startswith(prefix_zh):
                parts = detail.split(':', 1)
                return parts[1].strip() if len(parts) > 1 else detail
            if lang != 'zh' and detail.startswith(prefix_en):
                parts = detail.split(':', 1)
                return parts[1].strip() if len(parts) > 1 else detail
            return detail

        msg = None
        exc_type = type(e)

        if isinstance(e, NameError):
            detail = strip_prefix(base_msg, 'NameError', '名称错误')
            msg = fmt('NameError', detail)
            exc_type = NameError
        elif isinstance(e, ZeroDivisionError):
            msg = fmt('ZeroDivisionError')
            exc_type = ZeroDivisionError
        elif isinstance(e, IndexError):
            msg = fmt('IndexError')
            exc_type = IndexError
        elif isinstance(e, KeyError):
            msg = fmt('KeyError', base_msg)
            exc_type = LocalizedKeyError
        elif isinstance(e, TypeError):
            detail = strip_prefix(base_msg, 'TypeError', '类型错误')
            if lang == 'zh':
                if 'can only concatenate str (not ' in detail and ' to str' in detail:
                    detail = '只能将字符串与非字符串连接。请检查操作数类型是否都是字符串'
                elif 'unsupported operand type(s) for +' in detail:
                    detail = detail.replace('unsupported operand type(s) for +', '不支持的操作数类型用于 +')
                elif 'can only concatenate list (not ' in detail and ' to list' in detail:
                    detail = detail.replace('can only concatenate list (not ', '只能将列表与列表连接（不能与 ').replace(' to list', ' 连接）')
            msg = fmt('TypeError', detail)
            exc_type = TypeError
        elif isinstance(e, ValueError):
            detail = strip_prefix(base_msg, 'ValueError', '值错误')
            if lang == 'zh' and 'codec can' in base_msg:
                detail = '文件编码错误，请使用 UTF-8 编码保存文件'
            msg = fmt('ValueError', detail)
            exc_type = ValueError
        elif isinstance(e, AttributeError):
            if lang == 'zh':
                detail = strip_prefix(base_msg, 'AttributeError', '')
                if "' 没有方法 '" in detail or "' has no method '" in detail:
                    msg = fmt('RuntimeError', detail)
                else:
                    msg = fmt('RuntimeError', detail)
            else:
                msg = fmt('RuntimeError', base_msg)
            exc_type = type(e)
        elif isinstance(e, SyntaxError):
            detail = strip_prefix(base_msg, 'SyntaxError', '语法错误')
            lower = detail.lower()
            if 'untermin' in lower:
                msg = fmt('UnterminatedString')
            elif 'unexpected end' in lower or 'eof' in lower:
                msg = fmt('UnexpectedEOF')
            elif 'indent' in lower:
                msg = fmt('InvalidIndent')
            else:
                msg = fmt('SyntaxError', detail)
        else:
            try:
                from .parser import ParserError
                if isinstance(e, ParserError):
                    detail = strip_prefix(base_msg, 'SyntaxError', '语法错误')
                    lower = detail.lower()
                    if 'untermin' in lower:
                        msg = fmt('UnterminatedString')
                    elif 'unexpected end' in lower or 'eof' in lower:
                        msg = fmt('UnexpectedEOF')
                    elif 'indent' in lower:
                        msg = fmt('InvalidIndent')
                    else:
                        msg = fmt('SyntaxError', detail)
            except Exception:
                pass


        if msg is None:
            if lang == 'zh' and 'maximum recursion depth exceeded' in base_msg:
                base_msg = '递归深度超过限制'
            msg = fmt('RuntimeError', base_msg)
            exc_type = type(e)
        
        # --- 添加源码行 + ^ 指向 ---
        if lineno is not None and hasattr(self, 'source_code') and self.source_code:
            lines = self.source_code.split('\n')
            if lineno - 1 < len(lines):
                src_line = lines[lineno - 1].replace('\t', '    ')
                col = original_col
                if col <= 0:
                    cause = getattr(e, '__cause__', None)
                    if cause:
                        col = getattr(cause, 'col', 0)
                if col > 0 and col <= len(src_line) + 1:
                    token_len = getattr(e, 'token_len', None)
                    if token_len is None:
                        import re
                        name_match = re.search(r"'([^']*)'", base_msg)
                        token_len = len(name_match.group(1)) if name_match else 1
                    pointer = ' ' * (col - 1) + '^' * token_len
                    displayed_line = src_line.rstrip()
                    msg = f"{msg}{loc}\n    {displayed_line}\n    {pointer}"
                else:
                    displayed_line = src_line.rstrip()
                    msg = f"{msg}{loc}\n    {displayed_line}"
        else:
            msg = f"{msg}{loc}"

        new_exc = exc_type(msg)
        new_exc.localized = True
        if lineno is not None:
            new_exc.lineno = lineno
        return new_exc

    def push_frame(self, frame: Dict[str, Any]):
        self.frames.append(frame)

    def pop_frame(self):
        self.frames.pop()

    def set_var(self, name: str, value: Any, global_: bool = False):
        if global_:
            self.frames[0][name] = value
        
        else:
            self.frames[-1][name] = value

    def find_var(self, name: str):
        for frame in reversed(self.frames):
            if name in frame:
                return frame[name]
        if settings.LANGUAGE == 'zh':
            raise NameError(f"名称错误: 名称 '{name}' 未定义")
        raise NameError(f"name '{name}' is not defined")

    def builtin_print(self, *args):
        print(*args)

    def exec_stmt(self, node):
        t = type(node).__name__
        if t == 'ExprStmt':
            self.eval_expr(node.expr)
        elif t == 'Assign':
            val = self.eval_expr(node.value)
            # 检查是否在全局帧有标记
            if node.target.id in self.frames[0].get('__globals__', set()):
                self.set_var(node.target.id, val, global_=True)
            else:
                self.set_var(node.target.id, val)
        elif t == 'Return':
            val = self.eval_expr(node.value) if node.value is not None else None
            if isinstance(val, list):
                val = tuple(val)
            raise ReturnSignal(val)
        elif t == 'Print':
            vals = [self.eval_expr(a) for a in node.args]
            self.builtin_print(*vals)
        elif t == 'If':
            cond = self.eval_expr(node.test)
            if cond:
                for s in node.body:
                    self.exec_stmt(s)
            elif node.orelse is not None:
                if isinstance(node.orelse, list):
                    for s in node.orelse:
                        self.exec_stmt(s)
                else:
                    try:
                        self.exec_stmt(node.orelse)
                    except (ReturnSignal, BreakSignal, ContinueSignal):
                        raise
                    except Exception as e:
                        lineno = getattr(node.orelse, 'lineno', None)
                        col = getattr(node.orelse, 'col', None)
                        if lineno:
                            e.lineno = lineno
                        if col:
                            e.col = col
                            e.token_len = getattr(node.orelse, 'token_len', 5)
                        raise
        elif t == 'While':
            while self.eval_expr(node.test):
                try:
                    for s in node.body:
                        self.exec_stmt(s)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif t == 'FuncDef':
            # Evaluate default expressions at function definition time in current environment
            defaults_values = {}
            if getattr(node, 'defaults', None):
                for k, v_node in node.defaults.items():
                    defaults_values[k] = self.eval_expr(v_node)
            func = Function(node.name, node.params, node.body, closure=self.frames[-1].copy(), defaults=defaults_values)
            self.set_var(node.name, func)
        elif t == 'Break':
            raise BreakSignal()
        elif t == 'Continue':
            raise ContinueSignal()
        elif t == 'For':
            iterable = self.eval_expr(node.iter)
            for item in iterable:
                # 支持解包: for x, y in dict.items()
                if isinstance(node.target, ast_nodes.ListNode):
                    # 多变量
                    for i, target in enumerate(node.target.elements):
                        if isinstance(item, (list, tuple)) and i < len(item):
                            self.set_var(target.id, item[i])
                        else:
                            self.set_var(target.id, item)
                else:
                    self.set_var(node.target.id, item)
                try:
                    for s in node.body:
                        try:
                            self.exec_stmt(s)
                        except (ReturnSignal, BreakSignal, ContinueSignal):
                            raise
                        except Exception as e:
                            lineno = getattr(s, 'lineno', None)
                            if lineno is None and hasattr(s, 'expr') and getattr(s.expr, 'lineno', None) is not None:
                                lineno = s.expr.lineno
                            new_exc = self._localize_exception(e, lineno)
                            if new_exc is e:
                                raise
                            raise new_exc from e
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif t == 'Global':
            for name in node.names:
                self.frames[0]['__globals__'].add(name)
        elif t == 'Try':
            try:
                for s in node.body:
                    self.exec_stmt(s)
            except Exception as e:
                handled = False
                for error_type, catch_body in node.catches:
                    if self._match_error(e, error_type):
                        for s in catch_body:
                            self.exec_stmt(s)
                        handled = True
                        break
                if not handled:
                    raise
            finally:
                if node.always_body:
                    for s in node.always_body:
                        self.exec_stmt(s)
        elif t == 'Import':
            import os
            filepath = node.filename
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.getcwd(), filepath)
            if not os.path.exists(filepath):
                exc = ImportError(f"找不到模块 '{node.filename}'")
                if hasattr(node, 'lineno'):
                    exc.lineno = node.lineno
                raise exc
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                if hasattr(node, 'col'):
                    e.col = node.col
                    e.token_len = len(node.filename.strip('"').strip("'"))  # +2 包含引号
                raise
            from .lexer import tokenize
            from .parser import Parser
            tokens = list(tokenize(code))
            p = Parser(tokens, source_code=code)
            mod = p.parse()
            for stmt in mod.body:
                self.exec_stmt(stmt)
        else:
            raise NotImplementedError(f"exec_stmt not implemented for {t}")

    def eval_expr(self, node):
        t = type(node).__name__
        if t == 'MethodCall':
            obj = self.eval_expr(node.obj)
            method_name = node.method
            args = [self.eval_expr(a) for a in node.args]
            # 对 list 的内置方法
            if isinstance(obj, list):
                if method_name == 'append':
                    obj.append(*args)
                    return None
                elif method_name == 'pop':
                    return obj.pop(*args)
            # 对 dict 的内置方法
            if isinstance(obj, dict):
                if method_name == 'keys':
                    return list(obj.keys())
                elif method_name == 'values':
                    return list(obj.values())
                elif method_name == 'items':
                    return list(obj.items())
            # 其他 Python 对象的方法，直接用 getattr
            method = getattr(obj, method_name, None)
            if method is not None and callable(method):
                return method(*args)
            exc = AttributeError(f"'{type(obj).__name__}' 没有方法 '{method_name}'")
            if hasattr(node, 'col'):
                exc.col = node.col
            exc.token_len = len(method_name) + 2  # xxx()
            raise exc

        if t == 'ListComp':
            iterable = self.eval_expr(node.iter)
            result = []
            for item in iterable:
                self.set_var(node.var, item)
                result.append(self.eval_expr(node.expr))
            return result
        
        if t == 'Number':
            return node.value
        if t == 'String':
            return node.value
        if t == 'ListNode':
            return [self.eval_expr(e) for e in node.elements]
        if t == 'DictNode':
            result = {}
            for k_node, v_node in node.pairs:
                k = self.eval_expr(k_node)
                v = self.eval_expr(v_node)
                result[k] = v
            return result
        if t == 'Name':
            try:
                return self.find_var(node.id)
            except NameError as e:
                # 附上 AST 节点的列号，用于错误 ^ 指向
                if hasattr(node, 'col'):
                    e.col = node.col
                raise
        if t == 'Subscript':
            val = self.eval_expr(node.value)
            idx = self.eval_expr(node.index)
            try:
                return val[idx]
            except Exception as e:
                if hasattr(node, 'col'):
                    e.col = node.col
                raise
        if t == 'BinaryOp':
            op = node.op
            # short-circuit aware binary ops
            if op == 'and':
                left = self.eval_expr(node.left)
                if not bool(left):
                    return False
                right = self.eval_expr(node.right)
                return bool(right)
            if op == 'or':
                left = self.eval_expr(node.left)
                if bool(left):
                    return True
                right = self.eval_expr(node.right)
                return bool(right)
            if op == 'xor':
                left = self.eval_expr(node.left)
                right = self.eval_expr(node.right)
                return bool(bool(left) ^ bool(right))
            if op == 'nand':
                left = self.eval_expr(node.left)
                if not bool(left):
                    # short-circuit: left False -> True
                    return True
                right = self.eval_expr(node.right)
                return not (bool(left) and bool(right))
            if op == 'nor':
                left = self.eval_expr(node.left)
                if bool(left):
                    # short-circuit: left True -> False
                    return False
                right = self.eval_expr(node.right)
                return not (bool(left) or bool(right))
            # arithmetic/comparison ops
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            try:
                if op == '+':
                    try:
                        return left + right
                    except TypeError:
                        return str(left) + str(right)
                if op == '-':
                    return left - right
                if op == '*':
                    return left * right
                if op == '/':
                    return left / right
                if op == '%':
                    return left % right
            except TypeError as e:
                if hasattr(node, 'right'):
                    if hasattr(node.right, 'col'):
                        e.col = node.right.col
                    if hasattr(node.right, 'value'):
                        e.token_len = len(str(node.right.value))
                elif hasattr(node, 'col'):
                    e.col = node.col
                raise
            except ZeroDivisionError as e:
                if hasattr(node, 'right'):
                    if hasattr(node.right, 'col'):
                        e.col = node.right.col
                    if hasattr(node.right, 'value'):
                        e.token_len = len(str(node.right.value))
                elif hasattr(node, 'col'):
                    e.col = node.col
                raise
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            if op == '<':
                return left < right
            if op == '>':
                return left > right
            if op == '<=':
                return left <= right
            if op == '>=':
                return left >= right
            if op == 'in':
                return left in right
            if op == 'not_in':
                return left not in right
            raise NotImplementedError(f"Binary op {op} not implemented")
        if t == 'UnaryOp':
            if node.op == 'not':
                val = self.eval_expr(node.operand)
                return not bool(val)
            val = self.eval_expr(node.operand)
            if node.op == '+':
                return +val
            if node.op == '-':
                return -val
            raise NotImplementedError(f"Unary op {node.op} not implemented")
        if t == 'Call':
            if isinstance(node.func, ast_nodes.Name):
                fname = node.func.id
                fn = self.find_var(fname)
            else:
                fn = self.eval_expr(node.func)
            args = [self.eval_expr(a) for a in node.args]
            kwargs = {}
            if hasattr(node, 'kwargs') and node.kwargs:
                for k, v in node.kwargs.items():
                    kwargs[k] = self.eval_expr(v)
            if isinstance(fn, Function):
                try:
                    return fn.call(self, args)
                except Exception as e:
                    if hasattr(node, 'col'):
                        e.col = node.col
                    # 计算整个调用的长度：函数名 + ( + 参数 + )
                    if hasattr(node, 'func') and hasattr(node.func, 'col'):
                        call_str = str(node.func.id) + '(' + ', '.join(str(a) for a in args) + ')'
                        e.token_len = len(call_str)
                    raise
            if callable(fn):
                if kwargs:
                    return fn(*args, **kwargs)
                return fn(*args)
            if settings.LANGUAGE == 'zh':
                raise TypeError(f"类型错误: 对象不可调用: {fn}")
            raise TypeError(f"{fn} is not callable")
        raise NotImplementedError(f"eval_expr not implemented for {t}")

    def run_module(self, module: ast_nodes.Module):
        for i, stmt in enumerate(module.body):
            try:
                self.exec_stmt(stmt)
            except Exception as e:
                # annotate/localize and re-raise with lineno if available
                lineno = getattr(e, 'lineno', None) or getattr(stmt, 'lineno', None)
                if lineno is None:
                    lineno = i + 1
                new_exc = self._localize_exception(e, lineno)
                if new_exc is e:
                    raise
                raise new_exc from e
    def builtin_sort(self, arr, mode='auto', reverse=False, verbose=False):
        if not isinstance(arr, list):
            raise TypeError(f"sort() 需要列表，而不是 {type(arr).__name__}")

        if mode == 'benchmark':
            return self._benchmark_sorts(arr, reverse)

        if mode == 'auto':
            n = len(arr)
            if n <= 16:
                mode = 'insertion'
            elif n <= 1000:
                mode = 'quick'
            else:
                mode = 'tim'

        arr_copy = arr[:]
        steps = [0]

        if verbose:
            print(f"📊 排序算法: {mode}")
            print(f"📋 原始数组: {arr_copy}")
            print(f"📏 数组长度: {len(arr_copy)}")

        if mode == 'native':
            result = sorted(arr_copy, reverse=reverse)
        elif mode == 'bubble':
            result = self._bubble_sort(arr_copy, reverse, steps)
        elif mode == 'selection':
            result = self._selection_sort(arr_copy, reverse, steps)
        elif mode == 'insertion':
            result = self._insertion_sort(arr_copy, reverse, steps)
        elif mode == 'merge':
            result = self._merge_sort(arr_copy, reverse, steps)
        elif mode == 'quick':
            result = self._quick_sort(arr_copy, reverse, steps)
        elif mode == 'heap':
            result = self._heap_sort(arr_copy, reverse, steps)
        elif mode == 'counting':
            result = self._counting_sort(arr_copy, reverse, steps)
        elif mode == 'radix':
            result = self._radix_sort(arr_copy, reverse, steps)
        elif mode == 'bucket':
            result = self._bucket_sort(arr_copy, reverse, steps)
        elif mode == 'tim':
            result = sorted(arr_copy, reverse=reverse)
        elif mode == 'intro':
            result = sorted(arr_copy, reverse=reverse)
        else:
            raise ValueError(f"不支持的排序模式: {mode}")

        if verbose:
            print(f"✅ 排序完成，共 {steps[0]} 步")
            print(f"📋 排序结果: {result}")

        return result
    def builtin_sum(self, iterable):
        try:
            return sum(iterable)
        except Exception as e:
            raise TypeError(f"sum() 需要可迭代对象: {e}")

    def builtin_max(self, *args):
        if len(args) == 1:
            try:
                return max(args[0])
            except Exception:
                pass
        return max(args)

    def builtin_min(self, *args):
        if len(args) == 1:
            try:
                return min(args[0])
            except Exception:
                pass
        return min(args)

    def builtin_type(self, obj):
        return type(obj).__name__

    def builtin_input(self, prompt=''):
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        return sys.stdin.readline().rstrip('\n')
    
    def _benchmark_sorts(self, arr, reverse):
        import time
        modes = ['native', 'bubble', 'selection', 'insertion', 'merge', 'quick', 'heap', 'counting', 'radix', 'bucket']
        results = {}
        
        print("🏁 排序算法性能对比")
        print(f"{'算法':<12} {'时间(ms)':<12} {'步数':<10} {'结果正确':<10}")
        print("-" * 50)
        
        expected = sorted(arr, reverse=reverse)
        
        for mode in modes:
            arr_copy = arr[:]
            steps = [0]
            start = time.perf_counter()
            try:
                if mode == 'native':
                    result = sorted(arr_copy, reverse=reverse)
                elif mode == 'bubble':
                    result = self._bubble_sort(arr_copy, reverse, steps)
                elif mode == 'selection':
                    result = self._selection_sort(arr_copy, reverse, steps)
                elif mode == 'insertion':
                    result = self._insertion_sort(arr_copy, reverse, steps)
                elif mode == 'merge':
                    result = self._merge_sort(arr_copy, reverse, steps)
                elif mode == 'quick':
                    result = self._quick_sort(arr_copy, reverse, steps)
                elif mode == 'heap':
                    result = self._heap_sort(arr_copy, reverse, steps)
                elif mode == 'counting':
                    result = self._counting_sort(arr_copy, reverse, steps)
                elif mode == 'radix':
                    result = self._radix_sort(arr_copy, reverse, steps)
                elif mode == 'bucket':
                    result = self._bucket_sort(arr_copy, reverse, steps)
                elapsed = (time.perf_counter() - start) * 1000
                correct = "✅" if result == expected else "❌"
                results[mode] = elapsed
                print(f"{mode:<12} {elapsed:>8.3f} ms {steps[0]:>8}  {correct:<10}")
            except Exception as e:
                print(f"{mode:<12} {'错误':>12}  {str(e)[:20]}")
        
        return results

    def _bubble_sort(self, arr, reverse, steps=None):
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if steps: steps[0] += 1
                if (arr[j] > arr[j + 1]) != reverse:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

    def _selection_sort(self, arr, reverse, steps=None):
        n = len(arr)
        for i in range(n):
            idx = i
            for j in range(i + 1, n):
                if steps: steps[0] += 1
                if (arr[j] < arr[idx]) != reverse:
                    idx = j
            arr[i], arr[idx] = arr[idx], arr[i]
        return arr

    def _insertion_sort(self, arr, reverse, steps=None):
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and (arr[j] > key) != reverse:
                if steps: steps[0] += 1
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr

    def _merge_sort(self, arr, reverse, steps=None):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = self._merge_sort(arr[:mid], reverse, steps)
        right = self._merge_sort(arr[mid:], reverse, steps)
        return self._merge(left, right, reverse, steps)

    def _merge(self, left, right, reverse, steps=None):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if steps: steps[0] += 1
            if (left[i] < right[j]) != reverse:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    def _quick_sort(self, arr, reverse, steps=None):
        if len(arr) <= 1:
            return arr
        if steps: steps[0] += len(arr)
        pivot = arr[len(arr) // 2]
        if reverse:
            left = [x for x in arr if x > pivot]
            middle = [x for x in arr if x == pivot]
            right = [x for x in arr if x < pivot]
        else:
            left = [x for x in arr if x < pivot]
            middle = [x for x in arr if x == pivot]
            right = [x for x in arr if x > pivot]
        return self._quick_sort(left, reverse, steps) + middle + self._quick_sort(right, reverse, steps)

    def _heap_sort(self, arr, reverse, steps=None):
        import heapq
        if steps: steps[0] += len(arr)
        if reverse:
            return list(heapq.merge([-x for x in arr]))
        return sorted(arr)

    def _counting_sort(self, arr, reverse, steps=None):
        if not arr:
            return arr
        max_val = max(arr)
        min_val = min(arr)
        count = [0] * (max_val - min_val + 1)
        for x in arr:
            if steps: steps[0] += 1
            count[x - min_val] += 1
        result = []
        rng = range(min_val, max_val + 1)
        if reverse:
            rng = reversed(rng)
        for i in rng:
            result.extend([i] * count[i - min_val])
        return result

    def _radix_sort(self, arr, reverse, steps=None):
        if not arr:
            return arr
        max_val = max(arr)
        exp = 1
        while max_val // exp > 0:
            if steps: steps[0] += len(arr)
            arr = self._counting_sort_by_digit(arr, exp, steps)
            exp *= 10
        return arr[::-1] if reverse else arr

    def _counting_sort_by_digit(self, arr, exp, steps=None):
        n = len(arr)
        output = [0] * n
        count = [0] * 10
        for i in range(n):
            if steps: steps[0] += 1
            count[(arr[i] // exp) % 10] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        for i in range(n - 1, -1, -1):
            digit = (arr[i] // exp) % 10
            output[count[digit] - 1] = arr[i]
            count[digit] -= 1
        return output

    def _bucket_sort(self, arr, reverse, steps=None):
        if not arr:
            return arr
        n = len(arr)
        buckets = [[] for _ in range(n)]
        for x in arr:
            if steps: steps[0] += 1
            idx = int(n * (x - min(arr)) / (max(arr) - min(arr) + 1))
            buckets[min(idx, n - 1)].append(x)
        result = []
        for b in buckets:
            result.extend(sorted(b, reverse=reverse))
        return result