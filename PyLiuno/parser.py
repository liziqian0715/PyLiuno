"""Recursive-descent parser for PyLiuno"""
from typing import List
from .lexer import Token
from . import ast

from . import settings
import json
import os

# load i18n resource for parser-localized details
_i18n_path = os.path.join(os.path.dirname(__file__), 'i18n.json')
try:
    with open(_i18n_path, 'r', encoding='utf-8') as _f:
        _I18N = json.load(_f)
except Exception:
    _I18N = {'en': {'SyntaxError': '{detail}{loc}'}, 'zh': {'SyntaxError': '{detail}{loc}'}}

class ParserError(Exception):
    def __init__(self, key_or_msg, token: Token = None, **kwargs):
        # Attach token location when available
        self.lineno = token.line if token else None    #
        self.col = token.col if token else None         #
        lang = settings.LANGUAGE if hasattr(settings, 'LANGUAGE') else 'en'
        if token is not None:
            loc = f"第{token.line}行第{token.col}列" if lang == 'zh' else f"(line {token.line}, col {token.col})"
        else:
            loc = ''
        lang = settings.LANGUAGE if hasattr(settings, 'LANGUAGE') else 'en'
        templates = _I18N.get(lang, _I18N.get('en', {}))

        def _token_display(tkn):
            
            lang = settings.LANGUAGE if hasattr(settings, 'LANGUAGE') else 'en'
            if not isinstance(tkn, Token):
                return str(tkn) if tkn is not None else ''
            
            # 关键字显示为关键字名
            keyword_names = {'PRINT', 'DEF', 'IF', 'ELIF', 'ELSE', 'WHILE', 'FOR', 
                           'RETURN', 'BREAK', 'CONTINUE', 'IN',
                           'AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR'}
            if tkn.type in keyword_names:
                return f"'{tkn.value}'" if lang == 'zh' else f"'{tkn.value}'"
            # 特殊 token
            if tkn.type == 'NEWLINE':
                return '换行符' if lang == 'zh' else 'NEWLINE'
            if tkn.type == 'INDENT':
                return '缩进' if lang == 'zh' else 'INDENT'
            if tkn.type == 'DEDENT':
                return '缩进结束' if lang == 'zh' else 'DEDENT'
            if tkn.type == 'EOF':
                return '文件结束' if lang == 'zh' else 'EOF'
            if tkn.type == 'NAME':
                return f"'{tkn.value}'" if lang == 'zh' else f"NAME('{tkn.value}')"
            if tkn.type == 'NUMBER':
                return f"数字 {tkn.value}" if lang == 'zh' else f"NUMBER({tkn.value})"
            if tkn.type == 'STRING':
                return f"\"{tkn.value}\"" if lang == 'zh' else f"STRING(\"{tkn.value}\")"
            
            # 友好的符号名称
            friendly_names = {
                'OP': {
                    '=': "等号 '='", '+': "加号 '+'", '-': "减号 '-'", 
                    '*': "乘号 '*'", '/': "除号 '/'", '%': "取模 '%'",
                    '==': "双等号 '=='", '!=': "不等号 '!='",
                    '<': "小于号 '<'", '>': "大于号 '>'",
                    '<=': "小于等于 '<='", '>=': "大于等于 '>='",
                },
                'LPAREN': "左括号 '('",
                'RPAREN': "右括号 ')'",
                'LBRACKET': "左方括号 '['",
                'RBRACKET': "右方括号 ']'",
                'LBRACE': "左大括号 '{'",
                'RBRACE': "右大括号 '}'",
                'COLON': "冒号 ':'",
                'COMMA': "逗号 ','",
                'DOT': "点号 '.'",
            }
            
            if tkn.type in friendly_names:
                info = friendly_names[tkn.type]
                if isinstance(info, dict):
                    return info.get(tkn.value, f"{tkn.type}('{tkn.value}')")
                return info if lang == 'zh' else f"{tkn.type}('{tkn.value}')"
            
            # 其他未覆盖的 token
            return f"{tkn.type}('{tkn.value}')"

        def render(template, **kwargs):
            result = template.format(**kwargs)
            return result + (' ' + loc if loc else '')

        # Handle structured keys
        if key_or_msg == 'expected':
            expected = kwargs.get('expected')
            got = kwargs.get('got')
            got_str = _token_display(got)

            # 翻译期望的 token 名称
            expected_names = {
                'LPAREN': "左括号 '('",
                'RPAREN': "右括号 ')'",
                'COLON': "冒号 ':'",
                'COMMA': "逗号 ','",
                'NEWLINE': '换行符',
                'INDENT': '缩进',
                'DEDENT': '缩进结束',
                'NAME': '名称',
                'NUMBER': '数字',
                'STRING': '字符串',
            }
            expected_display = expected_names.get(expected, expected) if lang == 'zh' else expected

            prev_token = kwargs.get('prev_token', None)
            context = ""
            if prev_token and lang == 'zh':
                prev_display = _token_display(prev_token)
                if expected == 'LPAREN':
                    context = f"{prev_display} 后面缺少 "
                elif expected == 'RPAREN':
                    context = f"这里缺少 "
                elif expected == 'COLON':
                    context = f"这里缺少 "
                else:
                    context = f"期望 "
            else:
                context = "期望 " if lang == 'zh' else "Expected "
            
            # 选择模板
            if expected == 'RPAREN':
                tpl = templates.get('MissingRParen') or templates.get('ExpectedToken') or templates.get('SyntaxError')
                full_msg = render(tpl, expected=expected_display, got=got_str)
            elif expected == 'COLON':
                tpl = templates.get('MissingColon') or templates.get('ExpectedToken') or templates.get('SyntaxError')
                full_msg = render(tpl, expected=expected_display, got=got_str)
            else:
                tpl = templates.get('ExpectedToken') or templates.get('SyntaxError')
                # 如果有上下文，用更友好的格式
                if context and lang == 'zh' and expected == 'LPAREN':
                    if lang == 'zh':
                        detail = f"{context}{expected_display}"
                    else:
                        detail = f"Expected {expected_display} after {prev_token.value if prev_token else ''}"
                    full_msg = detail + (' ' + loc) if loc else detail
                else:
                    full_msg = render(tpl, expected=expected_display, got=got_str)
            super().__init__(full_msg)
            return

        if key_or_msg == 'assignment_in_call':
            t = token
            token_str = _token_display(t)
            tpl = templates.get('AssignmentInCall') or templates.get('SyntaxError')
            full_msg = render(tpl, token=token_str)
            super().__init__(full_msg)
            return

        if key_or_msg in ('unexpected', 'unexpected_in_primary'):
            t = token
            token_str = _token_display(t)
            tpl = templates.get('UnexpectedToken') or templates.get('SyntaxError')
            full_msg = render(tpl, token=token_str, detail=token_str)
            super().__init__(full_msg)
            return

        if key_or_msg == 'unexpected_eof':
            tpl = templates.get('UnexpectedEOF') or templates.get('SyntaxError')
            full_msg = render(tpl, detail='')
            super().__init__(full_msg)
            return

        if key_or_msg == 'invalid_indent':
            tpl = templates.get('InvalidIndent') or templates.get('SyntaxError')
            full_msg = render(tpl, detail='')
            super().__init__(full_msg)
            return

        if key_or_msg == 'unterminated_string':
            tpl = templates.get('UnterminatedString') or templates.get('SyntaxError')
            full_msg = render(tpl, detail='')
            super().__init__(full_msg)
            return

        # default: literal message
        detail = str(key_or_msg)
        syntax_tpl = templates.get('SyntaxError', '{detail}{loc}')
        full_msg = render(syntax_tpl, detail=detail)
        super().__init__(full_msg)

class Parser:
    def __init__(self, tokens, source_code: str = None):
        self.tokens = list(tokens)
        self.pos = 0
        self.current = self.tokens[0]
        self._last_token = None
        self.source_code = source_code  # 保存源码

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = Token('EOF', '', -1, -1)

    def expect(self, ttype):
        if self.current.type == ttype:
            val = self.current
            self.advance()
            self._last_token = val
            return val
        # If we hit EOF while expecting a token, prefer unexpected EOF message
        if self.current.type == 'EOF':
            raise ParserError('unexpected_eof', token=self.current)
        if ttype == 'INDENT' and self.current.type != 'INDENT':
            raise ParserError('invalid_indent', token=self.current)
        raise ParserError('expected', token=self.current, expected=ttype, got=self.current, prev_token=getattr(self, '_last_token', None))

    def parse(self):
        body = []
        while self.current.type != 'EOF':
            if self.current.type == 'NEWLINE':
                self.advance(); continue
            body.append(self.parse_stmt())
        mod = ast.Module(body)
        # attach lineno for module as 1
        setattr(mod, 'lineno', 1)
        return mod

    def parse_stmt(self):
        if self.current.type == 'GLOBAL':
            tok = self.current
            self.advance()
            names = []
            names.append(self.expect('NAME').value)
            while self.current.type == 'COMMA':
                self.advance()
                names.append(self.expect('NAME').value)
            if self.current.type == 'NEWLINE': self.advance()
            node = ast.Global(names)
            setattr(node, 'lineno', tok.line)
            return node
        if self.current.type == 'IMPORT':
            tok = self.current
            self.advance()
            # import "filename.pyl" 或 import filename
            if self.current.type == 'STRING':
                filename = self.current.value
                file_tok = self.current
                self.advance()
            elif self.current.type == 'NAME':
                filename = self.current.value + '.pyl'
                file_tok = self.current
                self.advance()
            else:
                raise ParserError('expected', token=self.current, expected='STRING', got=self.current)
            if self.current.type == 'NEWLINE': self.advance()
            node = ast.Import(filename)
            setattr(node, 'lineno', tok.line)
            setattr(node, 'col', file_tok.col + 1)
            return node
        if self.current.type == 'DEF':
            return self.parse_funcdef()
        if self.current.type == 'IF':
            return self.parse_if()
        if self.current.type == 'WHILE':
            return self.parse_while()
        if self.current.type == 'FOR':
            return self.parse_for()
        if self.current.type == 'BREAK':
            br_tok = self.current
            self.advance()
            if self.current.type == 'NEWLINE': self.advance()
            node = ast.Break()
            setattr(node, 'lineno', br_tok.line)
            return node
        if self.current.type == 'CONTINUE':
            ct_tok = self.current
            self.advance()
            if self.current.type == 'NEWLINE': self.advance()
            node = ast.Continue()
            setattr(node, 'lineno', ct_tok.line)
            return node
        if self.current.type == 'RETURN':
            ret_tok = self.current
            self.advance()
            # 支持多值返回: return expr1, expr2, ...
            exprs = []
            exprs.append(self.parse_expr())
            while self.current.type == 'COMMA':
                self.advance()
                exprs.append(self.parse_expr())
            if self.current.type == 'NEWLINE': self.advance()
            if len(exprs) == 1:
                node = ast.Return(exprs[0])
            else:
                node = ast.Return(ast.ListNode(exprs))
            setattr(node, 'lineno', ret_tok.line)
            return node
        if self.current.type == 'PRINT':
            return self.parse_print()
        if self.current.type == 'NAME':
            nxt = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
            if nxt and nxt.type == 'OP' and nxt.value == '=':
                name = self.current.value
                name_tok = self.current
                self.advance()
                self.advance()
                expr = self.parse_expr()
                if self.current.type == 'NEWLINE': self.advance()
                target = ast.Name(name)
                setattr(target, 'col', name_tok.col)     # 列号
                node = ast.Assign(target, expr)
                setattr(node, 'lineno', name_tok.line)
                return node
        expr = self.parse_expr()
        if self.current.type == 'NEWLINE': self.advance()
        node = ast.ExprStmt(expr)
        # attach lineno if possible
        if hasattr(expr, 'lineno'):
            setattr(node, 'lineno', expr.lineno)
        return node

    def parse_print(self):
        print_tok = self.expect('PRINT')  # 用 expect 保存 _last_token
        self.expect('LPAREN')
        args = []
        if self.current.type != 'RPAREN':
            args.append(self.parse_expr())
            while self.current.type == 'COMMA':
                self.advance()
                args.append(self.parse_expr())
        if self.current.type == 'OP' and self.current.value == '=':
            raise ParserError('assignment_in_call', token=self.current)
        self.expect('RPAREN')
        if self.current.type == 'NEWLINE': self.advance()
        node = ast.Print(args)
        setattr(node, 'lineno', print_tok.line)
        return node

    def parse_funcdef(self):
        def_tok = self.expect('DEF')
        name_tok = self.expect('NAME')
        name = name_tok.value
        self.expect('LPAREN')
        params = []
        defaults = {}
        if self.current.type == 'NAME':
            # parse first param (may have default)
            while True:
                p_tok = self.expect('NAME')
                p_name = p_tok.value
                if self.current.type == 'OP' and self.current.value == '=':
                    # default value
                    self.advance()
                    default_node = self.parse_expr()
                    defaults[p_name] = default_node
                params.append(p_name)
                if self.current.type == 'COMMA':
                    self.advance()
                    if self.current.type == 'NAME':
                        continue
                    else:
                        break
                else:
                    break
        self.expect('RPAREN')
        self.expect('COLON')
        body = self.parse_block()
        node = ast.FuncDef(name, params, body, defaults if defaults else None)
        setattr(node, 'lineno', def_tok.line)
        return node

    def parse_if(self):
        if_tok = self.expect('IF')
        test = self.parse_expr()
        self.expect('COLON')
        body = self.parse_block()
        orelse = None
        # support ELIF chains by turning them into nested If nodes in orelse
        if self.current.type == 'ELIF':
            # build the chained If nodes for each ELIF
            head = None
            last = None
            while self.current.type == 'ELIF':
                elif_tok = self.expect('ELIF')
                elif_test = self.parse_expr()
                self.expect('COLON')
                elif_body = self.parse_block()
                new_if = ast.If(elif_test, elif_body, None)
                setattr(new_if, 'lineno', elif_tok.line)
                setattr(new_if, 'col', elif_tok.col + 5)  # 跳过 'elif '
                setattr(new_if, 'token_len', 5)
                # 计算条件长度（从 elif 后到 : 前）
                # elif_test 是 AST 节点，用 _expr_len 估算
                if head is None:
                    head = new_if
                    last = new_if
                else:
                    # attach as the orelse of the previous elif
                    last.orelse = new_if
                    last = new_if
            # optional ELSE after ELIF chain
            if self.current.type == 'ELSE':
                else_tok = self.expect('ELSE')
                self.expect('COLON')
                last.orelse = self.parse_block()
            orelse = head
        elif self.current.type == 'ELSE':
            else_tok = self.expect('ELSE')
            self.expect('COLON')
            orelse = self.parse_block()
        node = ast.If(test, body, orelse)
        setattr(node, 'lineno', if_tok.line)
        return node

    def parse_while(self):
        while_tok = self.expect('WHILE')
        test = self.parse_expr()
        self.expect('COLON')
        body = self.parse_block()
        node = ast.While(test, body)
        setattr(node, 'lineno', while_tok.line)
        return node

    def parse_for(self):
        # FOR NAME IN expr ':' block
        for_tok = self.expect('FOR')
        name_tok = self.expect('NAME')
        target = ast.Name(name_tok.value)
        setattr(target, 'lineno', name_tok.line)
        setattr(target, 'col', name_tok.col)     # 列号
        self.expect('IN')
        iter_expr = self.parse_expr()
        self.expect('COLON')
        body = self.parse_block()
        node = ast.For(target, iter_expr, body)
        setattr(node, 'lineno', for_tok.line)
        return node

    def parse_block(self):
        self.expect('NEWLINE')
        self.expect('INDENT')
        stmts = []
        while self.current.type not in ('DEDENT', 'EOF'):
            if self.current.type == 'NEWLINE':
                self.advance(); continue
            stmt = self.parse_stmt()
            # if stmt has no lineno, try to set from current token
            if not hasattr(stmt, 'lineno') and self.current is not None:
                try:
                    setattr(stmt, 'lineno', self.current.line)
                except Exception:
                    pass
            stmts.append(stmt)
        self.expect('DEDENT')
        return stmts

    # Expression parsing
    def parse_expr(self):
        return self.parse_or()

    # boolean operator precedence: or -> and -> not -> comparisons
    def parse_or(self):
        node = self.parse_xor()
        while self.current.type in ('OR', 'NOR'):
            op_tok = self.current
            op_type = self.current.type
            self.advance()
            right = self.parse_xor()
            if op_type == 'OR':
                node = ast.BinaryOp(node, 'or', right)
            else:
                node = ast.BinaryOp(node, 'nor', right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_xor(self):
        node = self.parse_and()
        while self.current.type == 'XOR':
            op_tok = self.current
            self.advance()
            right = self.parse_and()
            node = ast.BinaryOp(node, 'xor', right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.current.type in ('AND', 'NAND'):
            op_tok = self.current
            op_type = self.current.type
            self.advance()
            right = self.parse_not()
            if op_type == 'AND':
                node = ast.BinaryOp(node, 'and', right)
            else:
                node = ast.BinaryOp(node, 'nand', right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_not(self):
        if self.current.type == 'NOT':
            op_tok = self.current
            self.advance()
            operand = self.parse_not()
            node = ast.UnaryOp('not', operand)
            setattr(node, 'lineno', op_tok.line)
            return node
        return self.parse_equality()

    def parse_equality(self):
        node = self.parse_comparison()
        while self.current.type == 'OP' and self.current.value in ('==', '!='):
            op_tok = self.current
            op = self.current.value
            self.advance()
            right = self.parse_comparison()
            node = ast.BinaryOp(node, op, right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.current.type == 'OP' and self.current.value in ('<', '>', '<=', '>='):
            op_tok = self.current
            op = self.current.value
            self.advance()
            right = self.parse_term()
            node = ast.BinaryOp(node, op, right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current.type == 'OP' and self.current.value in ('+', '-'):
            op_tok = self.current
            op = self.current.value
            self.advance()
            right = self.parse_factor()
            node = ast.BinaryOp(node, op, right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.current.type == 'OP' and self.current.value in ('*', '/', '%'):
            op_tok = self.current
            op = self.current.value
            self.advance()
            right = self.parse_unary()
            node = ast.BinaryOp(node, op, right)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
        return node

    def parse_unary(self):
        if self.current.type == 'OP' and self.current.value in ('+', '-'):
            op_tok = self.current
            op = self.current.value
            self.advance()
            operand = self.parse_unary()
            node = ast.UnaryOp(op, operand)
            setattr(node, 'lineno', op_tok.line)
            setattr(node, 'col', op_tok.col)
            return node
        return self.parse_primary()

    def parse_primary(self):
        t = self.current
        if t.type == 'NUMBER':
            self.advance()
            node = ast.Number(t.value)
            setattr(node, 'lineno', t.line)
            setattr(node, 'col', t.col)
            return node
        if t.type == 'STRING':
            self.advance()
            node = ast.String(t.value)
            setattr(node, 'lineno', t.line)
            setattr(node, 'col', t.col + 1)  # +1 跳过左引号，指向实际内容
            return node
        if t.type in ('TRUE', 'FALSE', 'NONE'):
            # represent literals as names that resolve to pre-defined globals in the interpreter
            mapping = {'TRUE': 'True', 'FALSE': 'False', 'NONE': 'None'}
            name = mapping[t.type]
            self.advance()
            node = ast.Name(name)
            setattr(node, 'lineno', t.line)
            setattr(node, 'col', t.col)
            return node
        if t.type == 'NAME':
            name = t.value
            self.advance()
            node = ast.Name(name)
            setattr(node, 'lineno', t.line)
            setattr(node, 'col', t.col)     # 加上列号
            # call
            if self.current.type == 'LPAREN':
                lp_tok = self.current
                self.advance()
                args = []
                kwargs = {}
                if self.current.type != 'RPAREN':
                    # 检查是否为 name=expr
                    if self.current.type == 'NAME':
                        # 看下一个 token 是不是 =
                        nxt = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
                        if nxt and nxt.type == 'OP' and nxt.value == '=':
                            key = self.expect('NAME').value
                            self.expect('OP')  # =
                            val = self.parse_expr()
                            kwargs[key] = val
                        else:
                            args.append(self.parse_expr())
                    else:
                        args.append(self.parse_expr())
                    while self.current.type == 'COMMA':
                        self.advance()
                        if self.current.type == 'NAME':
                            nxt = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
                            if nxt and nxt.type == 'OP' and nxt.value == '=':
                                key = self.expect('NAME').value
                                self.expect('OP')
                                val = self.parse_expr()
                                kwargs[key] = val
                                continue
                        args.append(self.parse_expr())
                if self.current.type == 'OP' and self.current.value == '=':
                    raise ParserError('assignment_in_call', token=self.current)
                self.expect('RPAREN')
                node = ast.Call(node, args, kwargs if kwargs else None)
                setattr(node, 'lineno', lp_tok.line)
                setattr(node, 'col', node.func.col)  # 用函数名的列号
            # subscription e.g., a[0]
            while self.current.type == 'LBRACKET':
                lb = self.current
                self.advance()
                idx = self.parse_expr()
                self.expect('RBRACKET')
                node = ast.Subscript(node, idx)
                setattr(node, 'lineno', lb.line)
                setattr(node, 'col', getattr(idx, 'col', lb.col))  # 用键的列号
            while self.current.type == 'DOT':
                dot_tok = self.current
                self.advance()
                method_tok = self.expect('NAME')
                method_name = method_tok.value
                self.expect('LPAREN')
                args = []
                if self.current.type != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.current.type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expr())
                self.expect('RPAREN')
                method_node = ast.Name(method_name)
                setattr(method_node, 'lineno', method_tok.line)
                setattr(method_node, 'col', method_tok.col)
                node = ast.MethodCall(node, method_name, args)
                setattr(node, 'lineno', dot_tok.line)
                setattr(node, 'col', getattr(method_node, 'col', dot_tok.col))
            return node
        if t.type == 'LPAREN':
            self.advance()
            expr = self.parse_expr()
            self.expect('RPAREN')
            node = expr
            # support subscription after grouping
            while self.current.type == 'LBRACKET':
                lb = self.current
                self.advance()
                idx = self.parse_expr()
                self.expect('RBRACKET')
                node = ast.Subscript(node, idx)
                setattr(node, 'lineno', lb.line)
                setattr(node, 'col', lb.col)
                            # method call e.g., lst.append(1)
            while self.current.type == 'DOT':
                dot_tok = self.current
                self.advance()
                method_tok = self.expect('NAME')
                method_name = method_tok.value
                self.expect('LPAREN')
                args = []
                if self.current.type != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.current.type == 'COMMA':
                        self.advance()
                        args.append(self.parse_expr())
                self.expect('RPAREN')
                method_node = ast.Name(method_name)
                setattr(method_node, 'lineno', method_tok.line)
                setattr(method_node, 'col', method_tok.col)
                node = ast.MethodCall(node, method_name, args)
                setattr(node, 'lineno', dot_tok.line)
                setattr(node, 'col', getattr(method_node, 'col', dot_tok.col))
            return node
        if t.type == 'LBRACKET':
            lb = self.current
            self.advance()
            if self.current.type == 'RBRACKET':
                self.expect('RBRACKET')
                node = ast.ListNode([])
                setattr(node, 'lineno', lb.line)
                return node
            first = self.parse_expr()
            # 检测列表推导式: [expr for var in iterable]
            if self.current.type == 'FOR':
                self.advance()
                var_tok = self.expect('NAME')
                self.expect('IN')
                iter_expr = self.parse_expr()
                self.expect('RBRACKET')
                node = ast.ListComp(first, var_tok.value, iter_expr)
                setattr(node, 'lineno', lb.line)
                setattr(node, 'col', lb.col)
                return node
            # 普通列表
            elements = [first]
            while self.current.type == 'COMMA':
                self.advance()
                elements.append(self.parse_expr())
            self.expect('RBRACKET')
            node = ast.ListNode(elements)
            setattr(node, 'lineno', lb.line)
            return node
        if t.type == 'LBRACE':
            # dict literal { key: value, ... }
            lb = self.current
            self.advance()
            pairs = []
            if self.current.type != 'RBRACE':
                # key
                key_node = self.parse_expr()
                self.expect('COLON')
                val_node = self.parse_expr()
                pairs.append((key_node, val_node))
                while self.current.type == 'COMMA':
                    self.advance()
                    key_node = self.parse_expr()
                    self.expect('COLON')
                    val_node = self.parse_expr()
                    pairs.append((key_node, val_node))
            self.expect('RBRACE')
            node = ast.DictNode(pairs)
            setattr(node, 'lineno', lb.line)
            return node
        # structured unexpected error so localization can present translated detail
        raise ParserError('unexpected_in_primary', token=t)
