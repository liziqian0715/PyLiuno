PyLiuno grammar (subset)

This file documents the core syntax and token semantics used by the PyLiuno parser.

Tokens
- NAME: identifier, e.g. my_var
- NUMBER: integer or float literal
- STRING: single- or double-quoted strings
- INDENT / DEDENT / NEWLINE: indentation control and line endings
- KEYWORDS: def, if, elif, else, while, for, in, break, continue, return, print, True, False, None,
  and, or, not, xor, nand, nor
- Operators: + - * / % == != < > <= >= =
- Delimiters: ( ) [ ] { } , :

Expressions (informal)
- Primary: NUMBER | STRING | NAME | ( expr ) | list literal | dict literal
- Call: primary '(' [expr (',' expr)*] ')'
- Subscription: primary '[' expr ']'

Operator precedence (low -> high)
1. or, nor
2. xor
3. and, nand
4. not
5. comparisons: == != < > <= >=
6. + -
7. * / %
8. unary + -
9. call, subscription, primary

Statements
- assignment: NAME '=' expr
- if: 'if' expr ':' block [ 'elif' expr ':' block ]* [ 'else' ':' block ]
- while: 'while' expr ':' block
- for: 'for' NAME 'in' expr ':' block
- def: 'def' NAME '(' [params] ')' ':' block
- return, break, continue, print

Builtins (selected)
- print(...)
- range(stop) | range(start, stop) | range(start, stop, step)
- len(obj)
- enumerate(iterable, start=0)
- str(x), int(x), float(x), bool(x), list(iterable)

Notes
- Logical operators (and, or, not, xor, nand, nor) evaluate to boolean values (True/False) and implement short-circuiting as described in the README.
- Function defaults are evaluated at function-definition time.
