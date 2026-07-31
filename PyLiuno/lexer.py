"""PyLiuno lexer module
Provides: Token, tokenize()
"""
from collections import namedtuple
import json
import os
import re
from . import settings

Token = namedtuple('Token', ['type', 'value', 'line', 'col'])

_i18n_path = os.path.join(os.path.dirname(__file__), 'i18n.json')
try:
    with open(_i18n_path, 'r', encoding='utf-8') as _f:
        _I18N = json.load(_f)
except Exception:
    _I18N = {
        'en': {
            'UnexpectedCharacter': 'Unexpected character: {char}',
            'UnterminatedString': 'Unterminated string'
        },
        'zh': {
            'UnexpectedCharacter': '意外的字符: {char}',
            'UnterminatedString': '未终止的字符串'
        }
    }


def _lex_error(key: str, **kwargs):
    lang = settings.LANGUAGE if hasattr(settings, 'LANGUAGE') else 'en'
    templates = _I18N.get(lang, _I18N.get('en', {}))
    tpl = templates.get(key)
    if tpl:
        return tpl.format(**kwargs)
    if key == 'UnexpectedCharacter':
        return f"Unexpected character: {kwargs.get('char')!r}"
    if key == 'UnterminatedString':
        return 'Unterminated string'
    return str(key)

_token_spec = [
    ('NUMBER',   r"\d+(?:\.\d+)?"),
    # simpler STRING pattern (non-greedy, line-limited)
    ('STRING',   r'".*?"|\'.*?\''),
    ('NAME',     r'[A-Za-z_][A-Za-z0-9_]*'),
    ('OP',       r'==|!=|<=|>=|->|[+\-*/%<>]=?|='),
    ('COLON',    r':'),
    ('COMMA',    r','),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('DOT',      r'\.'),
    ('SKIP',     r'[ \t]+'),
    ('MISMATCH', r'.'),
]
_token_regex = re.compile('|'.join('(?P<%s>%s)' % pair for pair in _token_spec))
KEYWORDS = {'def', 'if', 'elif', 'else', 'while', 'return', 'print', 'True', 'False', 'None', 'for', 'in', 'break', 'continue', 'and', 'or', 'not', 'xor', 'nand', 'nor', 'global','import'}


def tokenize(code):
    """Yield Token objects from source code string.
    Produces INDENT/DEDENT/NEWLINE and other tokens. Assumes indentation uses spaces.
    """
    lines = code.splitlines(True)
    indent_stack = [0]
    lineno = 0

    for raw_line in lines:
        lineno += 1
        if raw_line.strip() == '' or raw_line.lstrip().startswith('#'):
            continue
        leading = 0
        for ch in raw_line:
            if ch == ' ':
                leading += 1
            elif ch == '\t':
                leading += 4
            else:
                break
        trimmed = raw_line.lstrip(' \t')

        if leading > indent_stack[-1]:
            indent_stack.append(leading)
            yield Token('INDENT', '', lineno, 1)
        while leading < indent_stack[-1]:
            indent_stack.pop()
            yield Token('DEDENT', '', lineno, 1)

        pos = len(raw_line) - len(trimmed)
        line_text = trimmed.rstrip('\n')
        line_end = pos + len(line_text)
        mo = _token_regex.match
        while pos < line_end:
            m = mo(raw_line, pos)
            if not m:
                break
            kind = m.lastgroup
            value = m.group(kind)
            if kind == 'NUMBER':
                val = float(value) if '.' in value else int(value)
                yield Token('NUMBER', val, lineno, pos + 1)
            elif kind == 'STRING':
                s = value[1:-1]
                s = s.encode('utf-8').decode('unicode_escape')
                yield Token('STRING', s, lineno, pos + 1)
            elif kind == 'NAME':
                if value in KEYWORDS:
                    yield Token(value.upper(), value, lineno, pos + 1)
                else:
                    yield Token('NAME', value, lineno, pos + 1)
            elif kind == 'OP':
                yield Token('OP', value, lineno, pos + 1)
            elif kind == 'COLON':
                yield Token('COLON', value, lineno, pos + 1)
            elif kind == 'COMMA':
                yield Token('COMMA', value, lineno, pos + 1)
            elif kind == 'LPAREN':
                yield Token('LPAREN', value, lineno, pos + 1)
            elif kind == 'RPAREN':
                yield Token('RPAREN', value, lineno, pos + 1)
            elif kind == 'LBRACKET':
                yield Token('LBRACKET', value, lineno, pos + 1)
            elif kind == 'RBRACKET':
                yield Token('RBRACKET', value, lineno, pos + 1)
            elif kind == 'LBRACE':
                yield Token('LBRACE', value, lineno, pos + 1)
            elif kind == 'RBRACE':
                yield Token('RBRACE', value, lineno, pos + 1)
            elif kind == 'DOT':
                yield Token('DOT', value, lineno, pos + 1)
            elif kind == 'SKIP':
                pass
            elif kind == 'MISMATCH':
                # If a quote char is unmatched, report unterminated string
                if value in ('"', "'"):
                    msg = _lex_error('UnterminatedString')
                else:
                    msg = _lex_error('UnexpectedCharacter', char=value)
                # Lexer-level syntax errors include line information directly
                loc = f" 第{lineno}行" if settings.LANGUAGE == 'zh' else f" (line {lineno})"
                raise SyntaxError(msg + loc)
            pos = m.end()

        yield Token('NEWLINE', '', lineno, line_end + 1)

    while len(indent_stack) > 1:
        indent_stack.pop()
        yield Token('DEDENT', '', lineno + 1, 1)

    yield Token('EOF', '', lineno + 1, 1)
