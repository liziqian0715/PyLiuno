# PyLiuno

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions)


PyLiuno — a small educational programming language implemented in Python.

Quick start

- Run a single example:
  python -c "import PyLiuno, sys; code=open('PyLiuno/examples/hello.pyl').read(); tokens=PyLiuno.tokenize(code); p=PyLiuno.Parser(tokens); mod=p.parse(); interp=PyLiuno.Interpreter(); interp.run_module(mod)"

- Run tests:
  python -m unittest discover -v PyLiuno/tests

Examples

The examples directory contains small demo programs:

- examples/hello.pyl        — print a greeting
- examples/arithmetic.pyl   — variables and arithmetic
- examples/conditional.pyl  — if/else and simple functions
- examples/factorial.pyl    — recursive function example
- examples/while_loop.pyl   — while loop example

Project layout

- PyLiuno/
  - __init__.py          # package API
  - lexer.py             # tokenizer
  - parser.py            # recursive-descent parser
  - ast.py               # AST node classes
  - interpreter.py       # AST interpreter
  - examples/            # example programs
  - tests/               # unit tests

Local development / install

To install the package in editable mode (recommended for development):

1. From the project root (D:\\编程), run:

   pip install -e .

2. Then you can `import PyLiuno` from any script or run the examples as shown above.

Design notes

- Execution model: AST interpreter (chosen for simplicity and debuggability)
- Types: dynamic (runtime)
- Indentation-based blocks (similar to Python)

Next steps

- Expand standard library, improve error reporting, add CI, and refine packaging (pyproject.toml).

Changelog (recent)

- Lists support: list literals [a, b, c] and indexing a[0].
- Dictionaries: dict literals {'k': v, ...} and key access d['k'].
- For loops: basic for x in iterable: body implementation supporting lists and dicts.
- CLI: 'pyl' command with 'pyl run <file>' and 'pyl repl' (REPL).

Planned next features

- break / continue in loops (done — see examples below).
- Collection methods and iteration helpers (.items(), .values(), etc.)
- Better REPL (history, multi-line editing)

Break / Continue examples

Break example (stops loop when condition met):

example: examples/break_example.pyl

    a = [1, 2, 3, 4]
    s = 0
    for x in a:
        if x == 3:
            break
        s = s + x
    print(s)  # prints 3

Continue example (skips current iteration):

example: examples/continue_example.pyl

    a = [1, 2, 3, 4]
    s = 0
    for x in a:
        if x == 2:
            continue
        s = s + x
    print(s)  # prints 8

You can run these examples with the CLI:

    pyl run PyLiuno/examples/break_example.pyl
    pyl run PyLiuno/examples/continue_example.pyl

Recent additions

- Built-in converters: str(), int(), float(), bool(), list()
  - Use str(x) to produce string representations when concatenating with strings.
- More built-ins: range(), len(), enumerate(), print(), ...
- Custom logical operators: xor, nand, nor (with short-circuit semantics). See grammar.md for details.

Documentation

See grammar.md for updated syntax notes and operator precedence.

Internationalization (i18n)

- PyLiuno 支持中文错误提示：在 REPL 中使用 `:lang zh` 切换到中文错误消息，使用 `:lang en` 切回英文。
- 切换后运行时和语法错误将以中文显示，并包含行号和简短建议（例如未定义变量会提示检查拼写或是否赋值）。
