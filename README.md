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







markdown
# PyLiuno

PyLiuno —— 一个用 Python 实现的小型教学编程语言。

## 快速开始

运行单个示例：
```bash
python -c "import PyLiuno, sys; code=open('PyLiuno/examples/hello.pyl').read(); tokens=PyLiuno.tokenize(code); p=PyLiuno.Parser(tokens); mod=p.parse(); interp=PyLiuno.Interpreter(); interp.run_module(mod)"
运行测试：

bash
python -m unittest discover -v PyLiuno/tests
示例程序
examples/ 目录包含一些小型演示程序：

文件	说明
hello.pyl	打印问候语
arithmetic.pyl	变量和算术运算
conditional.pyl	if/else 条件判断和简单函数
factorial.pyl	递归函数示例
while_loop.pyl	while 循环示例
项目结构
text
PyLiuno/
├── __init__.py      # 包入口 API
├── lexer.py         # 词法分析器（分词）
├── parser.py        # 递归下降解析器
├── ast.py           # AST 抽象语法树节点类
├── interpreter.py   # AST 解释器
├── examples/        # 示例程序
└── tests/           # 单元测试
本地开发 / 安装
推荐以可编辑模式安装（便于开发）：

在项目根目录（D:\编程）下运行：

bash
pip install -e .
之后你就可以在任何脚本中导入 PyLiuno，或按上述方式运行示例。

设计要点
执行模型：AST 解释器（选择此方案是为了简洁性和可调试性）

类型系统：动态类型（运行时确定）

代码块：基于缩进（与 Python 类似）

后续计划
扩展标准库

改进错误报告

增加 CI 持续集成

完善打包配置（pyproject.toml）

更新日志（近期）
列表支持：列表字面量 [a, b, c] 和索引访问 a[0]

字典支持：字典字面量 {'k': v, ...} 和键访问 d['k']

for 循环：基本 for x in iterable: 循环体实现，支持列表和字典

CLI 命令行：pyl 命令，支持 pyl run <文件> 和 pyl repl（交互式环境）

计划中的新特性
break / continue 循环控制（已完成，见下方示例）

集合方法和迭代辅助（.items()、.values() 等）

更好的 REPL（历史记录、多行编辑）

break / continue 示例
break 示例（满足条件时终止循环）
examples/break_example.pyl：

python
a = [1, 2, 3, 4]
s = 0
for x in a:
    if x == 3:
        break
    s = s + x
print(s)  # 输出 3
continue 示例（跳过当前迭代）
examples/continue_example.pyl：

python
a = [1, 2, 3, 4]
s = 0
for x in a:
    if x == 2:
        continue
    s = s + x
print(s)  # 输出 8
使用 CLI 运行这些示例：

bash
pyl run PyLiuno/examples/break_example.pyl
pyl run PyLiuno/examples/continue_example.pyl
近期新增
内置类型转换函数：str()、int()、float()、bool()、list()

使用 str(x) 可以在字符串拼接时获得字符串表示

更多内置函数：range()、len()、enumerate()、print() 等

自定义逻辑运算符：xor、nand、nor（支持短路求值），详见 grammar.md

文档
语法细节和运算符优先级请参阅 grammar.md。

国际化（i18n）
PyLiuno 支持中文错误提示：

在 REPL 中输入 :lang zh 切换到中文错误消息

输入 :lang en 切回英文

切换后，运行时错误和语法错误将以中文显示，并包含行号和简短建议（例如未定义变量时会提示检查拼写或是否赋值）。